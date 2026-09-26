"""qlsc: build a semantic layer from a warehouse's query log, and ask it questions.

  qlsc extract                  the aggregated log and the catalog snapshot, from the warehouse
  qlsc build                    parse, load, variables, cluster, hierarchy, align (from <work>)
  qlsc parse | load | variables | cluster | hierarchy | align     one stage
  qlsc virtualize               a Neo4j Virtual Graph model of the rows, written from the semantic layer
  qlsc ask "question"           question -> semantic layer -> tables -> SQL, dry-run
    --cypher                    ... -> Cypher over the virtual graph instead, checked with EXPLAIN
    --run                       ... -> and the answer

Every command reads the estate's config from --config, or QLSC_CONFIG (environment or .env).
"""

from __future__ import annotations

import argparse
import sys

from qlsc import align, cluster, extract, hierarchy, load, navigate, parse, variables, virtualize
from qlsc.config import ConfigError
from qlsc.config import load as load_settings


def build(s, a) -> None:
    for title, step in (
        ("parse", lambda: parse.run(s, a.sample)),
        ("load", lambda: load.run(s, reset_graph=True)),
        ("variables", lambda: variables.run(s)),
        ("cluster", lambda: cluster.run(s)),
        ("hierarchy", lambda: hierarchy.run(s)),
        ("align", lambda: align.run(s)),
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

    p = sub.add_parser("parse", help="fingerprint and resolve the log through the parser service")
    p.add_argument("--sample", type=float, help="fraction of distinct texts, e.g. 0.05")
    p.set_defaults(func=lambda s, a: parse.run(s, a.sample))

    p = sub.add_parser("load", help="load the bottom layer into Neo4j")
    p.add_argument("--reset", action="store_true", help="delete everything in the target database first")
    p.set_defaults(func=lambda s, a: load.run(s, reset_graph=a.reset))

    for name, module, what in (
        ("variables", variables, "WCC over trusted joins -> Variables"),
        ("cluster", cluster, "Leiden over co-reads and lineage -> level-1 Semantic groups"),
    ):
        p = sub.add_parser(name, help=what)
        p.add_argument("--no-names", action="store_true", help="skip the LLM naming")
        p.set_defaults(func=lambda s, a, m=module: m.run(s, names=not a.no_names))

    sub.add_parser("hierarchy", help="Semantic levels 2 and up").set_defaults(
        func=lambda s, a: hierarchy.run(s)
    )
    sub.add_parser("align", help="link the designed catalog and ontology; the diff").set_defaults(
        func=lambda s, a: align.run(s)
    )

    p = sub.add_parser("virtualize", help="a Neo4j Virtual Graph model of the rows, from the semantic layer")
    p.add_argument("--no-views", action="store_true", help="write the model only; create no views")
    p.set_defaults(func=lambda s, a: virtualize.run(s, create_views=not a.no_views))

    p = sub.add_parser("ask", help="question -> semantic layer -> tables -> SQL")
    p.add_argument("question", nargs="+")
    p.add_argument("--no-sql", action="store_true", help="stop at the cohort; no SQL, no dry run")
    p.add_argument("--cypher", action="store_true", help="Cypher over the virtual graph instead of SQL")
    p.add_argument("--run", action="store_true", help="run the query and print the answer")
    p.set_defaults(
        func=lambda s, a: navigate.run(
            s, " ".join(a.question), sql=not a.no_sql, cypher=a.cypher, execute=a.run
        )
    )
    return ap


def main(argv: list[str] | None = None) -> int:
    a = parser().parse_args(argv)
    try:
        a.func(load_settings(a.config), a)
    except ConfigError as e:
        print(f"qlsc: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
