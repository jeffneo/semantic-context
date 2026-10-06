"""qlsc: build a semantic layer from a warehouse's query log, and ask it questions.

  qlsc extract                  the aggregated log and the catalog snapshot, from the warehouse
  qlsc build                    parse, load, variables, computations, cluster, hierarchy, align, requests
  qlsc parse | load | variables | cluster | hierarchy | align | requests     one stage
  qlsc virtualize               a Neo4j Virtual Graph model of the rows, written from the semantic layer
  qlsc ask "question"           question -> semantic layer -> tables -> the router's query, dry-run:
                                memory, else a precedent (the business's own query, its values set), else
                                compiled SQL, else free Cypher when it answers, else free SQL
    --sql | --cypher | --memory | --precedent ... -> that route only (Cypher over the virtual graph, checked
                                with EXPLAIN; memory, when it holds the whole answer)
    --run                       ... -> and the answer
    --as PRINCIPAL              ... on a principal's behalf: only what the warehouse lets them read, run as them
  qlsc remember LABEL KEY...    an entity's context, fetched from the virtual graph and kept in memory;
                                many entities' contexts fetched together, in one batch (KEY - : from stdin)
  qlsc recall LABEL KEY...      the same context: from memory while it holds, else fetched again, with
                                what your agent noted about it
  qlsc converse FILE            record a conversation (YAML) in the Context Memory model, running its tools
  qlsc distill                  skills from the agents' experience in memory: proposed, for a person to approve
  qlsc skills [--approve ID]    the skills you may see; approve a proposed one (--as the approver)
                                (KEY: the label's key, or property=value; --as PRINCIPAL, as for ask)

Every command reads the estate's config from --config, or QLSC_CONFIG (environment or .env).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from qlsc import (
    align,
    cluster,
    computations,
    converse,
    distill,
    extract,
    hierarchy,
    load,
    memory,
    navigate,
    okf,
    parse,
    requests,
    variables,
    virtualize,
)
from qlsc.config import ConfigError
from qlsc.config import load as load_settings
from qlsc.process import absorb as process_absorb
from qlsc.process import abstract as process_abstract
from qlsc.process import annotate as process_annotate
from qlsc.process import build as process_build
from qlsc.process import context as process_context
from qlsc.process import outcomes as process_outcomes
from qlsc.process import outlook as process_outlook
from qlsc.process import source as process_source
from qlsc.warehouse import WarehouseUnavailable


def build(s, a) -> None:
    for title, step in (
        ("parse", lambda: parse.run(s, a.sample)),
        ("load", lambda: load.run(s, reset_graph=True)),
        ("variables", lambda: variables.run(s)),
        ("computations", lambda: computations.run(s)),
        ("cluster", lambda: cluster.run(s)),
        ("hierarchy", lambda: hierarchy.run(s)),
        ("align", lambda: align.run(s)),
        ("requests", lambda: requests.run(s)),
    ):
        print(f"\n== {title}")
        step()


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="qlsc", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("-c", "--config", help="the estate's config file (default: QLSC_CONFIG)")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("extract", help="pull the aggregated log and the catalog snapshot")
    p.add_argument("--log-only", action="store_true")
    p.add_argument("--catalog-only", action="store_true")
    p.set_defaults(func=lambda s, a: extract.run(s, log=not a.catalog_only, catalog=not a.log_only))

    p = sub.add_parser("build", help="every stage after extract, from scratch")
    p.add_argument("--sample", type=float, help="parse only this fraction of distinct texts, e.g. 0.05")
    p.set_defaults(func=build)

    p = sub.add_parser("parse", help="fingerprint and resolve the log with the parser")
    p.add_argument("--sample", type=float, help="fraction of distinct texts, e.g. 0.05")
    p.set_defaults(func=lambda s, a: parse.run(s, a.sample))

    p = sub.add_parser("load", help="load the bottom layer into Neo4j")
    p.add_argument("--reset", action="store_true", help="delete everything in the target database first")
    p.set_defaults(func=lambda s, a: load.run(s, reset_graph=a.reset))

    for name, module, what in (
        ("variables", variables, "WCC over trusted joins -> Variables"),
        ("cluster", cluster, "Leiden over co-reads and lineage -> level-1 Semantic groups"),
        ("computations", computations, "measures, dimensions and populations the log's queries compute"),
    ):
        p = sub.add_parser(name, help=what)
        p.add_argument("--no-names", action="store_true", help="skip the LLM naming")
        p.set_defaults(func=lambda s, a, m=module: m.run(s, names=not a.no_names))

    sub.add_parser(
        "requests", help="the request bank: what the business asks of the queries it runs"
    ).set_defaults(func=lambda s, a: requests.run(s))
    sub.add_parser("hierarchy", help="Semantic levels 2 and up").set_defaults(
        func=lambda s, a: hierarchy.run(s)
    )
    sub.add_parser("align", help="link the designed catalog and ontology; the diff").set_defaults(
        func=lambda s, a: align.run(s)
    )

    p = sub.add_parser("virtualize", help="a Neo4j Virtual Graph model of the rows, from the semantic layer")
    p.add_argument("--no-views", action="store_true", help="write the model only; create no views")
    p.set_defaults(func=lambda s, a: virtualize.run(s, create_views=not a.no_views))

    p = sub.add_parser("okf", help="the Computations as an Open Knowledge Format bundle")
    p.add_argument("--out", type=Path, help="the bundle's directory (default: <work>/okf)")
    p.set_defaults(func=lambda s, a: okf.run(s, a.out))

    p = sub.add_parser("ask", help="question -> semantic layer -> tables -> the router's query")
    p.add_argument("question", nargs="+")
    p.add_argument("--no-sql", action="store_true", help="stop at the cohort; no query, no dry run")
    p.add_argument("--sql", action="store_true", help="the SQL route only, instead of the router's choice")
    p.add_argument("--cypher", action="store_true", help="Cypher over the virtual graph only")
    p.add_argument("--memory", action="store_true", help="from memory only: when it holds the whole answer")
    p.add_argument(
        "--precedent", action="store_true", help="a precedent only: the business's own query, its values set"
    )
    p.add_argument("--run", action="store_true", help="run the query and print the answer")
    p.add_argument(
        "--as",
        dest="as_",
        metavar="PRINCIPAL",
        help="on a principal's behalf (a name in entitlements.principals, or the warehouse's own): "
        "only what the warehouse lets them read, run as them",
    )
    route = lambda a: (
        "none"
        if a.no_sql
        else "cypher"
        if a.cypher
        else "memory"
        if a.memory
        else "precedent"
        if a.precedent
        else "sql"
        if a.sql
        else "auto"
    )
    p.set_defaults(
        func=lambda s, a: navigate.run(s, " ".join(a.question), route(a), execute=a.run, as_=a.as_)
    )
    for name, what, force in (
        ("remember", "an entity's context, fetched from the virtual graph and kept in memory", True),
        ("recall", "an entity's context: from memory while it holds, else fetched and kept", False),
    ):
        p = sub.add_parser(name, help=what)
        p.add_argument("label", help="a label of the virtual graph")
        p.add_argument(
            "keys",
            nargs="+",
            metavar="key",
            help="its key, or property=value (another property that identifies one); several are fetched "
            "together, in one batch; - reads them from stdin",
        )
        p.add_argument("--full", action="store_true", help="every node of the context, not only the counts")
        p.add_argument(
            "--as",
            dest="as_",
            metavar="PRINCIPAL",
            help="on a principal's behalf: fetched as them, and only what they fetched and may read now",
        )
        p.set_defaults(
            func=lambda s, a, force=force: memory.run(s, a.label, a.keys, force=force, full=a.full, as_=a.as_)
        )
    sub.add_parser("distill", help="skills from the agents' experience in memory, proposed").set_defaults(
        func=lambda s, a: distill.run(s, distill_now=True)
    )
    p = sub.add_parser("skills", help="the skills you may see; --approve a proposed one")
    p.add_argument("--approve", metavar="ID", help="approve a proposed skill, by id or name")
    p.add_argument("--as", dest="as_", metavar="PRINCIPAL", help="as whom (the approver, or the reader)")
    p.set_defaults(func=lambda s, a: distill.run(s, approve_id=a.approve, as_=a.as_))
    p = sub.add_parser(
        "process", help="the State-Action graph from text (stages are added as they are built)"
    )
    stages = p.add_subparsers(dest="stage", required=True)
    stages.add_parser("read", help="read process.events and say what is in it").set_defaults(
        func=lambda s, a: process_source.summary(s)
    )
    stages.add_parser(
        "build", help="group the annotated turns into States and Actions and write the process database"
    ).set_defaults(func=lambda s, a: process_build.report(s))
    p = stages.add_parser(
        "context", help="a conversation's customer's context as of the call, and the rows its turns are about"
    )
    p.add_argument("conversation", help="a conversation_id in process.events")
    p.add_argument("--turn", type=int, help="link only what the turns up to this sequence say")
    p.add_argument("--as-of", help="a day (YYYY-MM-DD), instead of the call's own")
    p.set_defaults(func=lambda s, a: process_context.report(s, a.conversation, a.turn, a.as_of))
    stages.add_parser(
        "abstract", help="build the levels above the first level of States and Actions"
    ).set_defaults(func=lambda s, a: process_abstract.report(s))
    p = stages.add_parser(
        "outcomes",
        help="how each conversation ended, from its end and the agent's note, and the kinds of outcome",
    )
    p.add_argument("--limit", type=int, help="the first N conversations (a trial)")
    p.add_argument("--model", help="an LLM model id, or `query` for llm.query_model (default llm.model)")
    p.set_defaults(func=lambda s, a: process_outcomes.report(s, a.limit, a.model))
    stages.add_parser(
        "absorb",
        help="the odds each State and Action carries of a case ending well, and in which kind of outcome (no calls)",
    ).set_defaults(func=lambda s, a: process_absorb.report(s))
    p = stages.add_parser(
        "outlook",
        help="where a conversation stands at a turn, what reps did next from States like it and how those cases ended",
    )
    p.add_argument("conversation", help="a conversation_id in process.events")
    p.add_argument(
        "--turn", type=int, help="read the conversation only up to this sequence (a case in progress)"
    )
    p.add_argument(
        "--with-context",
        action="store_true",
        help="and the customer's context as of the call, from the warehouse",
    )
    p.set_defaults(func=lambda s, a: process_outlook.report(s, a.conversation, a.turn, a.with_context))
    p = stages.add_parser("annotate", help="describe each turn as a State or an Action, by an LLM")
    p.add_argument(
        "--unit",
        choices=["turn", "conversation"],
        default="turn",
        help="one call per turn, or per conversation",
    )
    p.add_argument("--limit", type=int, help="the first N conversations (a trial)")
    p.add_argument("--model", help="an LLM model id, or `query` for llm.query_model (default llm.model)")
    p.set_defaults(func=lambda s, a: process_annotate.report(s, a.unit, a.limit, a.model))
    p = sub.add_parser("converse", help="record a conversation (a YAML file) in the Context Memory model")
    p.add_argument("file", help="the conversation: title, messages, the tools each called, what was learned")
    p.add_argument(
        "--as", dest="as_", metavar="PRINCIPAL", help="on a principal's behalf (else the file's `as`)"
    )
    p.set_defaults(func=lambda s, a: converse.record(s, a.file, as_=a.as_))
    return ap


def main(argv: list[str] | None = None) -> int:
    a = parser().parse_args(argv)
    try:
        a.func(load_settings(a.config), a)
    except (
        ConfigError,
        memory.Unsupported,
        WarehouseUnavailable,
        process_source.SourceError,
        process_context.ContextError,
    ) as e:
        print(f"qlsc: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
