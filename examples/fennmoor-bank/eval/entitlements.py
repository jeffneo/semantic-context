"""Entitlements, checked with the warehouse as the oracle (plans/2026-09-27-entitlements.md; the pass-through,
plans/2026-09-28-jdbc-passthrough.md).

For each test principal (the estate's entitlements.principals, set up by entitlements/setup.py), each gold
question and a few probes, by both routes and the router, through the gateway (`qlsc ask --as`):
  1. rows: a SQL answer is what the principal's own read of the same query returns (run again as them,
     on a client built here), and where the estate's own read differs, the answer is the principal's: the
     row policy applied. A Cypher answer, with the pass-through on (virtualize.passthrough), ran as the
     principal: every job Virtual Graph ran for it is theirs in BigQuery's own job log, read here as the
     owner. Without it, the answer reads no table the warehouse filters per reader (the table's row
     policies, read here). Either way, a dry run of Virtual Graph's SQL as the principal passes.
  2. schema: no response, and no prompt sent to the LLM, names a table the principal can't read, a column
     hidden from them, a value the log filters either on, or a principal of the log. The oracle's allowlist
     is built here by dry runs as the principal: a different mechanism from the gateway's permission checks.
  3. negative controls: deliberately broken gateways, each of which checks 1 and 2 must catch, by name.
A leak (a hidden name, a row they can't read) is an incident; a question left unanswered is
over-restriction, counted apart.

Writes results/entitlements.md and .json. Prints a line per question as it goes.
Usage: uv run examples/fennmoor-bank/eval/entitlements.py [--controls-only | --rescore]
  (--rescore: the last run's schema checks, redone from the texts it saved under <work>/entitlements/)
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from common import RESULTS, SPEC, settings, write_result
from google.auth import impersonated_credentials
from google.cloud import bigquery
from match import ROWS

from qlsc import entitle, llm, navigate
from qlsc.graph import Graph
from qlsc.navigate import answer_cypher, answer_sql, pick, trace
from qlsc.warehouse import connect
from qlsc.warehouse.bigquery import SCOPE, GcloudCredentials

PROBES = {
    "P1": "How many customers do we have in each state?",
    "P2": "List the names and email addresses of our affluent customers.",
    "P3": "How many fraud alerts were raised in each channel?",
    "P4": "What is the average call handle time at each contact center site?",
    "P5": "Which customers, by CIF number, have the highest total deposit balances?",
    "P6": "How many card transactions did each customer segment make?",
}
# Each broken gateway, the principal and probes it is tried on, and the check that must catch it.
CONTROLS = {
    "navigation unfiltered (the trace shows everything; queries still run as the principal)": (
        ["contact-center", "marketing"],
        ["P3", "P4"],
        "schema",
    ),
    "hidden columns and their filter values shown": (["marketing"], ["P2", "P5"], "schema"),
    "SQL run as the estate, not the principal": (["risk"], ["P1", "P6"], "rows"),
    "the Cypher gate off (option A skipped)": (["risk"], ["P1", "P6"], "rows"),
}
# With the JDBC pass-through the gate's row-policy refusal no longer applies (the virtual graph reads as the
# principal), so its control is this one instead: the gateway signing every query as the data source.
PASSTHROUGH_CONTROLS = {
    "the gateway signs as the data source, not the principal": (["risk"], ["P1", "P6"], "rows"),
}
VG_JOBS = """
SELECT DISTINCT user_email FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time >= @since
  AND EXISTS (SELECT 1 FROM UNNEST(labels) l WHERE l.key = 'app' AND l.value = 'neo4j-virtual-graph')
  -- not the pool's liveness checks, nor Virtual Graph's key checks: no rows read
  AND TRIM(query) != 'SELECT 1'
  AND NOT REGEXP_CONTAINS(query, r'^SELECT 1 FROM `[^`]+`\.`[^`]+`\.`[^`]+` GROUP BY `[^`]+` HAVING COUNT\(\*\) > 1 LIMIT 1$')
"""
LAYER_TABLES = "MATCH (t:Table) WHERE t.in_catalog RETURN t.id AS t ORDER BY t"
LAYER_COLUMNS = (
    "MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) WHERE t.in_catalog RETURN t.id AS t, collect(c.name) AS cols"
)
VALUES = """
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)<-[f:FILTERS]-(:QueryShape) WHERE f.values IS NOT NULL
UNWIND f.values AS v
RETURN t.id AS t, c.name AS c, collect(DISTINCT v)[..200] AS vals
"""
PRINCIPALS = "MATCH (p:Principal) RETURN p.id AS id"


class Oracle:
    """What a principal may read, found here by dry runs as them, and their own reads of a query."""

    def __init__(self, s, who: str):
        self.s, self.who = s, who
        self.estate = connect(s)
        creds = impersonated_credentials.Credentials(
            source_credentials=GcloudCredentials(s["warehouse"]["gcloud_config"]),
            target_principal=who,
            target_scopes=[SCOPE],
            lifetime=3600,
        )
        self.client = bigquery.Client(project=s["warehouse"]["project"], credentials=creds, location="US")

    def dry(self, sql: str) -> bool:
        try:
            self.client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
            return True
        except Exception:
            return False

    def allowlist(self, tables: list[str], columns: dict[str, list[str]]) -> tuple[set, set]:
        """(readable tables, hidden columns of readable tables), by dry runs. LIMIT 1, never 0: BigQuery
        skips its column checks for a query it can prove returns nothing."""
        phys = lambda t: self.estate.physical_sql(f"SELECT 1 FROM `{t}`").split("FROM ", 1)[1].strip()
        deployed = json.loads((self.s.work / "catalog.json").read_text())["tables"]
        with ThreadPoolExecutor(16) as pool:
            ok = list(
                pool.map(lambda t: t in deployed and self.dry(f"SELECT 1 FROM {phys(t)} LIMIT 1"), tables)
            )
            readable = {t for t, x in zip(tables, ok) if x}
            whole = dict(
                zip(
                    sorted(readable),
                    pool.map(lambda t: self.dry(f"SELECT * FROM {phys(t)} LIMIT 1"), sorted(readable)),
                )
            )
            probe = [(t, c) for t, w in whole.items() if not w for c in columns.get(t, [])]
            seen = list(pool.map(lambda tc: self.dry(f"SELECT `{tc[1]}` FROM {phys(tc[0])} LIMIT 1"), probe))
        return readable, {tc for tc, x in zip(probe, seen) if not x}

    def read(self, sql: str) -> dict:
        """The query (logical names) run as the principal: {total, rows} | {error}."""
        try:
            job = self.client.query(
                self.estate.physical_sql(sql), job_config=bigquery.QueryJobConfig(maximum_bytes_billed=10**10)
            )
            result = job.result(max_results=ROWS)
            return {"total": result.total_rows, "rows": [dict(r.items()) for r in result]}
        except Exception as e:
            return {"error": str(getattr(e, "message", e))[:200]}

    def vg_readers(self, since: float) -> set[str]:
        """Who ran the jobs Virtual Graph sent since then, from BigQuery's own job log, read as the
        project's owner: the gateway can't write it."""
        owner = owner_client(self.s)
        config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("since", "TIMESTAMP", dt.datetime.fromtimestamp(since, dt.UTC))
            ]
        )
        for _ in range(6):  # the log trails the jobs by a few seconds
            got = {r["user_email"] for r in owner.query(VG_JOBS, job_config=config).result()}
            if got:
                return got
            time.sleep(5)
        return set()

    def row_policies(self, tables: list[str]) -> set[str]:
        """Tables with row access policies, read afresh from the warehouse (not the gateway's cache)."""
        out = set()
        for t in tables:
            ref = self.estate._physical_ref(t)
            if ref is None:
                continue
            got = self.estate.client._connection.api_request(
                method="GET",
                path=f"/projects/{ref.project}/datasets/{ref.dataset_id}/tables/{ref.table_id}/rowAccessPolicies",
            )
            if got.get("rowAccessPolicies"):
                out.add(t)
        return out


_OWNER = {}


def owner_client(s) -> bigquery.Client:
    """A client as the project's owner (entitlements/setup.py's credentials), for the job log."""
    if "client" not in _OWNER:
        path = Path(__file__).parent.parent / "entitlements" / "setup.py"
        spec = importlib.util.spec_from_file_location("fennmoor_entitlements_setup", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _OWNER["client"] = module.BQ
    return _OWNER["client"]


def canaries(G, s, readable: set[str], hidden: set) -> list[tuple[str, re.Pattern]]:
    """Names and values that must never appear for this principal: unreadable tables, hidden columns,
    the values the log filters them on, and every principal of the log."""
    tables = [r["t"] for r in G.rows(LAYER_TABLES)]
    cols = {r["t"]: r["cols"] for r in G.rows(LAYER_COLUMNS)}
    ok_names = {t.rsplit(".", 1)[-1].lower() for t in readable}
    ok_cols = {c.lower() for t in readable for c in cols.get(t, []) if (t, c) not in hidden}
    out = []
    word = lambda x, flags=re.I: re.compile(rf"(?<!\w){re.escape(x)}(?!\w)", flags)
    for t in tables:
        if t in readable:
            continue
        short = t.split(".", 1)[1]  # dataset.table
        out.append((f"table {short}", word(short)))
        name = t.rsplit(".", 1)[-1]
        if "_" in name and name.lower() not in ok_names and name.lower() not in ok_cols:
            out.append((f"table {name}", word(name)))
    for _t, c in sorted(hidden):
        if c.lower() not in ok_cols:
            out.append((f"column {c}", word(c)))
    shown = {(t, c) for t in readable for c in cols.get(t, []) if (t, c) not in hidden}
    ok_vals = {str(v) for r in G.rows(VALUES) if (r["t"], r["c"]) in shown for v in r["vals"]}
    for r in G.rows(VALUES):
        if (r["t"], r["c"]) in shown:
            continue
        for v in r["vals"]:
            v = str(v)
            if innocent(v) or v in ok_vals or v.lower() in ok_cols | ok_names:
                continue
            distinct = any(ch.isdigit() for ch in v) or "_" in v or (v.isupper() and len(v) >= 4)
            if len(v) >= 4 and distinct:
                out.append((f"value {v!r} of {r['t'].rsplit('.', 1)[-1]}.{r['c']}", word(v, 0)))
    for r in G.rows(PRINCIPALS):
        out.append((f"principal {r['id']}", word(r["id"])))
        local = r["id"].split("@")[0]
        if "." in local:  # a person's name
            out.append((f"principal {local}", word(local)))
    return out


# Values too common to mark anything: dates and periods (the calendar every prompt carries), SQL's own
# words and units, and small numbers (thresholds).
DATE_LIKE = re.compile(r"\d{4}(-\d{2}){0,2}([ T]\d{2}:\d{2}(:\d{2})?)?|\d{4}-?Q\d|\d{1,6}(\.\d+)?")
SQL_WORDS = {"MONTH", "WEEK", "DAY", "YEAR", "QUARTER", "HOUR", "DATE", "TRUE", "FALSE", "NULL", "ISOWEEK"}


def innocent(v: str) -> bool:
    return bool(DATE_LIKE.fullmatch(v)) or v.upper() in SQL_WORDS


def own_words(marks: list, question: str) -> list:
    """The canaries less those the question itself says: its words, or a name made of them
    ("contact center site" -> contact_center_site, which a writer may coin as an alias)."""
    words = set(re.findall(r"[a-z0-9]+", question.lower()))
    keep = []
    for label, rx in marks:
        name = label.split(" ", 1)[1].strip("'")
        if rx.search(question) or (
            label.startswith(("table ", "column ")) and set(name.lower().split("_")) <= words
        ):
            continue
        keep.append((label, rx))
    return keep


def rescore(G, s, res: dict, questions: dict) -> None:
    """The schema verdicts again, from the texts each question saved, with the canaries as they are now."""
    tables = [r["t"] for r in G.rows(LAYER_TABLES)]
    columns = {r["t"]: r["cols"] for r in G.rows(LAYER_COLUMNS)}
    for name, who in s["entitlements"]["principals"].items():
        oracle = Oracle(s, who)
        readable, hidden = oracle.allowlist(tables, columns)
        marks = canaries(G, s, readable, hidden)
        for q, r in res["runs"].get(name, {}).items():
            path = s.work / "entitlements" / f"{name}_{q}.json"
            if q == "oracle" or not path.exists():
                continue
            d = json.loads(path.read_text())
            m = own_words(marks, questions[q])
            r["schema"] = {
                route: scan(d["shown"] + json.dumps(seen(route, json.loads(text)), default=str), m)
                for route, text in d["answers"].items()
            }
            r["schema"]["prompts"] = scan("\n".join(d["prompts"]), m)


def seen(route: str, a: dict) -> dict:
    """What the gateway itself showed: a SQL answer's rows are the warehouse's own reply to the principal
    (a metadata query there lists what BigQuery lets them see), so they are the rows check's, not this one's."""
    if route == "sql" and a.get("result"):
        return a | {"result": {k: x for k, x in a["result"].items() if k != "rows"}}
    return a


def scan(text: str, marks: list) -> list[str]:
    return sorted({label for label, rx in marks if rx.search(text)})


def same(a: dict, b: dict) -> bool:
    """The same answer: the same total, and the same rows when they all came back."""
    if "error" in a or "error" in b or a.get("total") != b.get("total"):
        return False
    if a["total"] > len(a["rows"]):
        return True  # only the first rows came back, in an order the query may not fix
    # floats to 9 significant digits: two runs of an AVG may differ in the last ones
    norm = lambda x: float(f"{x:.9g}") if isinstance(x, float) else x
    key = lambda rows: sorted(
        json.dumps({k: norm(x) for k, x in r.items()}, sort_keys=True, default=str) for r in rows
    )
    return key(a["rows"]) == key(b["rows"])


def ask(G, s, question: str, allow, oracle: Oracle, marks: list, keep: Path | None = None) -> dict:
    """Both routes and the router, for one principal, with the checks. `keep`: where to save what was
    scanned, so the canaries can be refined and rescored without asking again."""
    marks = own_words(marks, question)
    prompts: list[str] = []
    call = llm.LLM.call

    def recorded(self, user, schema, tool, max_tokens=8000):
        prompts.append(self.system + "\n" + user)
        return call(self, user, schema, tool, max_tokens)

    llm.LLM.call = recorded
    try:
        tr = trace(G, s, question, allow=allow)
        answers = {"sql": answer_sql(G, s, tr, execute=True, rows=ROWS)}
        since = time.time() - 2
        answers["cypher"] = answer_cypher(G, s, tr, execute=True, rows=ROWS) | {"since": since}
    finally:
        llm.LLM.call = call
    shown = json.dumps({k: v for k, v in tr.items() if k != "allow"}, default=str)
    out = {"schema": {}, "rows": {}, "route": pick(answers["sql"], answers["cypher"])}
    for route, a in answers.items():  # the scan reads what was shown, never the rows the warehouse returned
        text = shown + json.dumps(
            {
                k: a.get(k)
                for k in ("sql", "cypher", "explanation", "declined", "refused", "check", "request")
            },
            default=str,
        )
        out["schema"][route] = scan(text, marks)
        out["rows"][route] = rows_check(route, a, oracle)
        out[route] = {
            "writer": a.get("writer"),
            "query": a.get("sql") or a.get("cypher"),
            "answered": navigate.answered(a),
            "why_not": a.get("refused")
            or a.get("declined")
            or a.get("skipped")
            or a.get("error")
            or (a.get("result") or {}).get("error")
            or (a.get("dry_run") or {}).get("error"),
        }
    out["schema"]["prompts"] = scan("\n".join(prompts), marks)
    if keep:
        keep.parent.mkdir(parents=True, exist_ok=True)
        keep.write_text(
            json.dumps(
                {
                    "shown": shown,
                    "answers": {r: json.dumps(answers[r], default=str) for r in answers},
                    "prompts": prompts,
                }
            )
        )
    return out


def rows_check(route: str, a: dict, oracle: Oracle) -> dict:
    if not navigate.answered(a) or (route == "sql" and "result" not in a):
        return {"verdict": "no answer"}
    if route == "sql":
        got = a["result"]
        mine, firms = (
            oracle.read(a["sql"]),
            oracle.estate._run(oracle.estate.physical_sql(a["sql"]), 10**10, ROWS),
        )
        firms = (
            {"total": firms.get("total"), "rows": firms.get("rows", [])} if firms.get("ok") else {"error": 1}
        )
        if not same({"total": got["total"], "rows": got["rows"]}, mine):
            return {"verdict": "INCIDENT", "why": "the answer isn't the principal's own read of its query"}
        filtered = not same(mine, firms)
        return {
            "verdict": "ok",
            "why": "the principal's rows"
            + (" (the firm's differ: the row policy applied)" if filtered else ""),
        }
    labels = {x for x in re.findall(r"\(\s*\w*\s*:\s*(\w+)", a["cypher"])}
    table = {r["label"]: r["table"] for r in GRAPH_LABELS}
    tables = sorted(table[x] for x in labels if x in table)
    if entitle.passthrough(oracle.s):  # the warehouse's own job log: as whom Virtual Graph read
        readers = oracle.vg_readers(a["since"])
        if not readers:
            return {"verdict": "unverified", "why": "no Virtual Graph job in the warehouse's log for it"}
        if readers != {oracle.who}:
            return {"verdict": "INCIDENT", "why": f"the virtual graph read as {', '.join(sorted(readers))}"}
    else:
        filtered = oracle.row_policies(tables)
        if filtered:
            return {
                "verdict": "INCIDENT",
                "why": f"the virtual graph read every row of {', '.join(sorted(filtered))}",
            }
    unreadable = [t for t in tables if t not in oracle.readable]  # the oracle's own allowlist
    props = set(re.findall(r"\b\w+\.(\w+)\b", a["cypher"]))
    hidden = sorted(c for t, c in oracle.hidden if t in tables and c in props)
    if unreadable or hidden:
        return {
            "verdict": "INCIDENT",
            "why": f"the virtual graph read {', '.join(unreadable + hidden)}, which the principal can't",
        }
    return {"verdict": "ok", "why": "no row-filtered table, and the principal reads all it reads"}


GRAPH_LABELS: list = []


def controls(s) -> dict:
    out = dict(CONTROLS)
    if entitle.passthrough(s):
        del out["the Cypher gate off (option A skipped)"]
        out |= PASSTHROUGH_CONTROLS
    return out


def driver_probes(s) -> dict:
    """Straight to the virtual graph, not through the gateway: the pass-through must refuse each."""
    q = "MATCH (c:Customer) RETURN count(*) AS n"
    p = s["entitlements"]["principals"]
    forged = entitle.token(s, p["marketing"]).split(".")[0] + "." + entitle.token(s, p["risk"]).split(".")[1]
    tries = {
        "no token (a Neo4j user reaching the virtual graph directly)": (q, {}),
        "a forged token (marketing's name, risk's signature)": (
            entitle.signed(q),
            {"qlsc_principal": forged},
        ),
        "an expired token": (
            entitle.signed(q),
            {"qlsc_principal": entitle.token(s, p["risk"], now=time.time() - 3600)},
        ),
    }
    out = {}
    with Graph(s, s["virtualize"]["neo4j"]) as V:
        for name, (cypher, params) in tries.items():
            try:
                V.capped(cypher, 10, **params)
                out[name] = {"refused": False}
            except Exception as e:
                why = str(getattr(e, "message", e))
                out[name] = {"refused": "qlsc pass-through: refused" in why, "why": why[:160]}
            print(f"  driver: {name}: {'refused' if out[name]['refused'] else 'NOT REFUSED'}", flush=True)
    return out


def broken(name: str):
    """A deliberately broken gateway: returns an undo."""
    saved = []

    def patch(obj, attr, value):
        saved.append((obj, attr, getattr(obj, attr)))
        setattr(obj, attr, value)

    if name.startswith("navigation unfiltered"):
        real = navigate.trace
        patch(
            navigate,
            "trace",
            lambda G, s, q, exclude=frozenset(), allow=None: real(G, s, q, exclude) | {"allow": allow},
        )
        patch(sys.modules[__name__], "trace", navigate.trace)
    elif name.startswith("hidden columns"):
        patch(entitle.Allowlist, "column", lambda self, t, c: t in self.tables)
        patch(entitle.Allowlist, "shown", lambda self, t, c: t in self.tables)
    elif name.startswith("SQL run as the estate"):
        patch(entitle, "warehouse", lambda s, allow: connect(s))
    elif name.startswith("the Cypher gate off"):
        patch(entitle, "check_cypher", lambda *a, **k: None)
    elif name.startswith("the gateway signs as the data source"):
        real = entitle.signing
        patch(entitle, "signing", lambda s, allow, cypher: real(s, None, cypher))
    return lambda: [setattr(o, a, v) for o, a, v in reversed(saved)]


def main() -> int:
    s = settings()
    controls_only = "--controls-only" in sys.argv
    only = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--only=")), "")
    if only:  # rerun some asks (principal:Q,...) into the last run's results
        return rerun(s, [tuple(x.split(":")) for x in only.split(",")])
    if "--rescore" in sys.argv:  # the last run, its schema checks redone from the texts it saved
        res = json.loads((RESULTS / "entitlements.json").read_text())
        gold = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
        with Graph(s) as G:
            rescore(G, s, res, {q: gold[q]["question"] for q in gold} | PROBES)
        return report(res)
    gold = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
    questions = {q: gold[q]["question"] for q in sorted(gold)} | PROBES
    res = {"runs": {}, "controls": {}}
    if entitle.passthrough(s):
        res["driver"] = driver_probes(s)
    with Graph(s) as G:
        GRAPH_LABELS.extend(G.rows(navigate.LABELS))
        tables = [r["t"] for r in G.rows(LAYER_TABLES)]
        columns = {r["t"]: r["cols"] for r in G.rows(LAYER_COLUMNS)}
        for name, who in s["entitlements"]["principals"].items():
            oracle = Oracle(s, who)
            readable, hidden = oracle.allowlist(tables, columns)
            oracle.readable, oracle.hidden = readable, hidden
            allow = entitle.allowlist(G, s, name, fresh=True)
            agree = readable == allow.tables and hidden == allow.hidden
            marks = canaries(G, s, readable, hidden)
            res["runs"][name] = {
                "oracle": {
                    "tables": len(readable),
                    "hidden": sorted(map(list, hidden)),
                    "agrees": agree,
                    "canaries": len(marks),
                }
            }
            print(
                f"{name}: the oracle finds {len(readable)} readable tables, {len(hidden)} hidden columns; "
                f"the gateway {'agrees' if agree else 'DISAGREES'}; {len(marks)} canaries",
                flush=True,
            )
            for control, (whom, probes, check) in controls(s).items():
                if name not in whom:
                    continue
                undo = broken(control)
                try:
                    caught = []
                    for q in probes:
                        r = ask(G, s, questions[q], allow, oracle, marks)
                        hit = (
                            any(r["schema"].values())
                            if check == "schema"
                            else any(x["verdict"] == "INCIDENT" for x in r["rows"].values())
                        )
                        caught.append((q, hit, r))
                finally:
                    undo()
                res["controls"].setdefault(control, []).append(
                    {
                        "principal": name,
                        "caught": any(h for _, h, _ in caught),
                        "by": check,
                        "detail": {q: r for q, _, r in caught},
                    }
                )
                print(
                    f"  control: {control}: {'CAUGHT' if any(h for _, h, _ in caught) else 'NOT CAUGHT'} ({check})",
                    flush=True,
                )
            if controls_only:
                continue
            for i, (q, text) in enumerate(questions.items(), 1):
                r = ask(G, s, text, allow, oracle, marks, s.work / "entitlements" / f"{name}_{q}.json")
                res["runs"][name][q] = r
                leaks = sorted({x for v in r["schema"].values() for x in v})
                rows = {k: v["verdict"] for k, v in r["rows"].items()}
                print(
                    f"  {i}/{len(questions)} {name} {q} routed={r['route']} rows={rows} leaks={leaks[:3]}",
                    flush=True,
                )
            (s.work / "entitlements.partial.json").write_text(
                json.dumps(res, default=str)
            )  # where a stopped run got to
    return report(res)


def rerun(s, which: list[tuple[str, str]]) -> int:
    res = json.loads((RESULTS / "entitlements.json").read_text())
    gold = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
    questions = {q: gold[q]["question"] for q in sorted(gold)} | PROBES
    with Graph(s) as G:
        GRAPH_LABELS.extend(G.rows(navigate.LABELS))
        tables = [r["t"] for r in G.rows(LAYER_TABLES)]
        columns = {r["t"]: r["cols"] for r in G.rows(LAYER_COLUMNS)}
        for name in dict.fromkeys(n for n, _ in which):
            who = s["entitlements"]["principals"][name]
            oracle = Oracle(s, who)
            oracle.readable, oracle.hidden = oracle.allowlist(tables, columns)
            allow = entitle.allowlist(G, s, name, fresh=True)
            marks = canaries(G, s, oracle.readable, oracle.hidden)
            for n, q in which:
                if n == name:
                    r = ask(
                        G, s, questions[q], allow, oracle, marks, s.work / "entitlements" / f"{name}_{q}.json"
                    )
                    res["runs"][name][q] = r
                    leaks = sorted({x for v in r["schema"].values() for x in v})
                    print(
                        f"  {name} {q} routed={r['route']} rows={ {k: v['verdict'] for k, v in r['rows'].items()} } leaks={leaks}",
                        flush=True,
                    )
        rescore(G, s, res, questions)
    return report(res)


def report(res: dict) -> int:
    L = ["# Entitlements, with the warehouse as the oracle", ""]
    L.append(
        "Each test principal through the gateway (`qlsc ask --as`), every gold question and six probes, by "
        "both routes (plans/2026-09-27-entitlements.md). **Schema**: no response or LLM "
        "prompt names what the principal can't read (the canaries: unreadable tables, hidden columns, their "
        "filter values, the log's principals). **Rows**: a SQL answer is the principal's own read of its "
        "query; "
        + (
            "a Cypher answer ran as the principal: every BigQuery job Virtual Graph ran for it is theirs in "
            "the warehouse's job log (the pass-through, plans/2026-09-28-jdbc-passthrough.md)."
            if "driver" in res
            else "a Cypher answer reads no row-filtered table and nothing the principal can't read."
        )
    )
    L += [
        "",
        "| principal | oracle agrees with the gateway | questions | schema leaks | row incidents | SQL answered | Cypher answered | Cypher refused | routed to Cypher |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name, run in res["runs"].items():
        qs = {q: r for q, r in run.items() if q != "oracle"}
        if not qs:
            continue
        leaks = sum(1 for r in qs.values() if any(r["schema"].values()))
        incidents = sum(1 for r in qs.values() for v in r["rows"].values() if v["verdict"] == "INCIDENT")
        n = lambda route, f, qs=qs: sum(1 for r in qs.values() if f(r[route]))
        L.append(
            f"| {name} | {'yes' if run['oracle']['agrees'] else 'NO'} | {len(qs)} | {leaks} | {incidents} | "
            f"{n('sql', lambda x: x['answered'])} | {n('cypher', lambda x: x['answered'])} | "
            f"{n('cypher', lambda x: 'filters the rows' in str(x['why_not']) or 'dry run' in str(x['why_not']))} | "
            f"{sum(1 for r in qs.values() if r['route'] == 'cypher')} |"
        )
    if res.get("driver"):
        L += ["", "## The pass-through, reached directly", "", "| query | refused |", "|---|---|"]
        L += [f"| {k} | {'yes' if x['refused'] else '**NO**'} |" for k, x in res["driver"].items()]
    L += [
        "",
        "## Negative controls: broken gateways the checks must catch",
        "",
        "| broken gateway | principal | caught | by |",
        "|---|---|---|---|",
    ]
    for control, tries in res["controls"].items():
        for t in tries:
            L.append(f"| {control} | {t['principal']} | {'yes' if t['caught'] else '**NO**'} | {t['by']} |")
    L += [
        "",
        "## Per question",
        "",
        "| principal | question | routed | SQL | Cypher | leaks |",
        "|---|---|---|---|---|---|",
    ]
    for name, run in res["runs"].items():
        for q, r in run.items():
            if q == "oracle":
                continue
            cell = lambda route, r=r: (
                f"{r['rows'][route]['verdict']}"
                + (f": {str(r[route]['why_not'])[:80]}" if not r[route]["answered"] else "")
            ).replace("|", "/")
            leaks = ", ".join(sorted({x for v in r["schema"].values() for x in v}))[:120]
            L.append(
                f"| {name} | {q} | {r['route']} | {cell('sql')} | {cell('cypher')} | {leaks or 'none'} |"
            )
    print(f"-> {write_result('entitlements', L, res)}")
    total = Counter()
    for run in res["runs"].values():
        for q, r in run.items():
            if q != "oracle":
                total["leaks"] += any(r["schema"].values())
                total["incidents"] += sum(v["verdict"] == "INCIDENT" for v in r["rows"].values())
    print(dict(total), {c: [t["caught"] for t in ts] for c, ts in res["controls"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
