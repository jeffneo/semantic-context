"""Execution accuracy: does `qlsc ask` get the right answer, by SQL and by Cypher over the virtual graph?

For each gold question, the question walks down the semantic layer to its cohort (qlsc's navigate),
and both routes write a query and run it:
  sql     SQL from the cohort, run in the warehouse
  cypher  Cypher over the virtual graph, from the cohort's tables that are labels there (plus one hop)
Each answer is compared with the question's reference answer (eval/reference/Qnn.sql, see answers.py),
or an accepted alternative reading of an ambiguous question (Qnn.*.sql), on the columns the reference
declares (`-- compare:`, with alternatives as a|b). The match is deterministic:
  - the same number of rows;
  - every compared column has a column in the answer with the same values, whatever its name;
  - the rows agree on those columns together.
Numbers match within 0.1% (or 0.01), and a share may come as a percentage; text ignoring case. An
answer pivoted on a compared column (one column per value) is melted back to rows first. Questions
whose reference compares nothing (open-ended or catalog questions) are run and shown, not scored.

Writes results/execution.md and .json.
Usage: uv run examples/fennmoor-bank/eval/execution.py [Q04 Q07 ...]
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from decimal import Decimal
from pathlib import Path

import yaml
from common import SPEC, settings, write_result

from qlsc.graph import Graph
from qlsc.navigate import answer_cypher, answer_sql, trace
from qlsc.warehouse import connect

REFERENCE = Path(__file__).resolve().parent / "reference"
MAXIMUM_BYTES_BILLED = 2 * 10**9
ROWS = 20000  # every gold answer has fewer (Q08's has 5,200: one row per campaign)
ROUTES = ("sql", "cypher")


def norm(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, int | float | Decimal):
        return float(v)
    if isinstance(v, dt.date | dt.datetime):
        return v.isoformat()[:10] if not isinstance(v, dt.datetime) else v.isoformat()
    if hasattr(v, "iso_format"):  # neo4j.time
        return v.iso_format()[:10]
    return str(v).strip().lower()


def same(a, b) -> bool:
    if isinstance(a, float) and isinstance(b, float):
        return abs(a - b) <= max(0.01, 1e-3 * max(abs(a), abs(b)))
    return a == b


def order(v):
    return (v is None, isinstance(v, str), v if v is not None else 0)


SCALES = (1.0, 100.0, 0.01)  # a share as a fraction or as a percentage


def scaled(xs: list, k: float) -> list:
    return [x * k if isinstance(x, float) else x for x in xs]


def scale_of(xs: list, ys: list) -> float | None:
    """The scale at which ys holds xs's values, if any."""
    for k in SCALES:
        a, b = sorted(scaled(xs, k), key=order), sorted(ys, key=order)
        if len(a) == len(b) and all(same(x, y) for x, y in zip(a, b)):
            return k
    return None


def compare(ref: dict, got: dict, items: list[list[str]]) -> tuple[str, str]:
    """-> (verdict, why): correct | wrong | empty. Each item is a column the answer must hold, or
    alternatives for it (branch_id|branch_name: either identifies the branch). A pivoted answer (one
    column per value of a compared dimension) is melted back to rows first."""
    if not got["rows"]:
        return "empty", "no rows"
    verdict = compare_rows(ref, got, items)
    if verdict[0] != "correct" and (melted := melt(ref, got, items)):
        again = compare_rows(ref, melted, items)
        if again[0] == "correct":
            return "correct", again[1] + " (pivoted)"
    return verdict


def compare_rows(ref: dict, got: dict, items: list[list[str]]) -> tuple[str, str]:
    if len(ref["rows"]) != len(got["rows"]):
        return "wrong", f"{len(got['rows'])} rows, not {len(ref['rows'])}"
    got_cols = {c: [norm(r.get(c)) for r in got["rows"]] for c in got["columns"]}
    mapping, scale, missing = {}, {}, []
    for alternatives in items:
        found = None
        for c in alternatives:
            if c not in ref["columns"]:
                continue
            ref_col = [norm(r[c]) for r in ref["rows"]]
            for g in got_cols:
                if g not in mapping.values() and (k := scale_of(ref_col, got_cols[g])) is not None:
                    found = (c, g, k, ref_col)
                    break
            if found:
                break
        if found:
            c, g, k, ref_col = found
            mapping[c], scale[c] = g, (k, ref_col)
        else:
            missing.append(alternatives)
    cols = list(mapping)
    ref_cols = {c: scaled(scale[c][1], scale[c][0]) for c in cols}
    ref_key = [tuple(ref_cols[c][i] for c in cols) for i in range(len(ref["rows"]))]
    got_key = [tuple(got_cols[mapping[c]][i] for c in cols) for i in range(len(got["rows"]))]
    relabels = {}
    for alternatives in list(missing) if cols else []:
        for c in alternatives:
            ref_col = [norm(r[c]) for r in ref["rows"]] if c in ref["columns"] else None
            if ref_col is None or not identifies(c, ref_col):
                continue
            g = next(
                (
                    g
                    for g in got_cols
                    if g not in mapping.values()
                    and g not in relabels.values()
                    and relabeled(ref_key, ref_col, got_key, got_cols[g])
                ),
                None,
            )
            if g:
                relabels[c] = g
                missing.remove(alternatives)
                break
    if missing:
        matched = len(mapping) + len(relabels)
        return "wrong", "no column holds " + ", ".join(
            "|".join(a) for a in missing
        ) + f" ({matched} of {len(items)} match)"
    key = lambda row: tuple(order(v) for v in row)
    ref_rows, got_rows = sorted(ref_key, key=key), sorted(got_key, key=key)
    if all(all(same(a, b) for a, b in zip(r, g)) for r, g in zip(ref_rows, got_rows)):
        return "correct", "matches on " + ", ".join(
            [f"{c}={mapping[c]}" if c != mapping[c] else c for c in cols]
            + [f"{c}~{g} (relabeled)" for c, g in relabels.items()]
        )
    return "wrong", "every column's values match, but not row by row"


IDENTIFIER = re.compile(r"(^|_)(id|key|code|number|num|no)$", re.I)


def identifies(name: str, values: list) -> bool:
    """A column that names things (text, or an identifier by its name) may be answered by another
    column naming the same things (a site's id by its name); a measure never is."""
    return all(v is None or isinstance(v, str) for v in values) or bool(IDENTIFIER.search(name))


def relabeled(ref_key: list[tuple], ref_vals: list, got_key: list[tuple], got_vals: list) -> bool:
    """Whether got_vals relabel ref_vals one to one, the rows paired by their other compared columns
    (the key). Rows the key doesn't tell apart only need the same number of values not yet paired."""
    if len(set(ref_vals)) != len(set(got_vals)):
        return False
    k = lambda row: tuple(order(v) for v in row[0])
    r, g = sorted(zip(ref_key, ref_vals), key=k), sorted(zip(got_key, got_vals), key=k)
    if not all(all(same(a, b) for a, b in zip(x[0], y[0])) for x, y in zip(r, g)):
        return False
    groups: list[tuple[list, list, tuple]] = []
    for x, y in zip(r, g):
        if groups and all(same(a, b) for a, b in zip(groups[-1][2], x[0])):
            groups[-1][0].append(x[1])
            groups[-1][1].append(y[1])
        else:
            groups.append(([x[1]], [y[1]], x[0]))
    fwd, back = {}, {}
    for rv, gv, _ in groups:
        if len(rv) == 1 and (fwd.setdefault(rv[0], gv[0]) != gv[0] or back.setdefault(gv[0], rv[0]) != rv[0]):
            return False
    for rv, gv, _ in groups:
        if len(rv) > 1:
            rest = list(gv)
            for a in rv:
                if a in fwd:
                    if fwd[a] not in rest:
                        return False
                    rest.remove(fwd[a])
            if len(rest) != sum(1 for a in rv if a not in fwd) or any(b in back for b in rest):
                return False
    return True


def melt(ref: dict, got: dict, items: list[list[str]]) -> dict | None:
    """An answer pivoted on a compared text column (DEPOSIT and CARD as deposit_closures and
    card_closures), melted back to one row per value; None if it isn't pivoted that way."""
    for alternatives in items:
        for d in alternatives:
            if d not in ref["columns"]:
                continue
            values = sorted({str(r[d]) for r in ref["rows"] if isinstance(r[d], str)})
            if not values or len(values) > 12:
                continue
            by_value = {}
            for v in values:
                cols = [c for c in got["columns"] if v.lower() in c.lower()]
                if len(cols) != 1:
                    break
                by_value[v] = cols[0]
            else:
                if len(set(by_value.values())) != len(values):
                    continue
                keep = [c for c in got["columns"] if c not in by_value.values()]
                rows = [
                    {**{c: r.get(c) for c in keep}, d: v, "_value": r.get(col)}
                    for r in got["rows"]
                    for v, col in by_value.items()
                ]
                return {"columns": [*keep, d, "_value"], "rows": rows}
    return None


def declared(sql: str) -> list[list[str]]:
    """The reference's `-- compare:` line: columns, each with its alternatives (a|b)."""
    m = re.search(r"^-- compare:\s*(.+)$", sql, re.M)
    text = m.group(1).strip() if m else "none"
    return [] if text.startswith("none") else [c.strip().split("|") for c in text.split(",")]


def references(wh, qid: str) -> list[dict]:
    """The question's reference answers: Qnn.sql, then any accepted alternative reading (Qnn.*.sql)."""
    out = []
    for path in [REFERENCE / f"{qid}.sql", *sorted(REFERENCE.glob(f"{qid}.*.sql"))]:
        sql = path.read_text()
        out.append(
            {"name": path.stem, "items": declared(sql), "result": wh.run(sql, MAXIMUM_BYTES_BILLED, ROWS)}
        )
    return out


def judge(refs: list[dict], got: dict) -> tuple[str, str]:
    """Correct if the answer matches any reference; otherwise the main reference's verdict."""
    verdicts = [(r["name"], compare(r["result"], got, r["items"])) for r in refs if r["items"]]
    for name, (v, why) in verdicts:
        if v == "correct":
            return v, why + ("" if "." not in name else f" (as {name})")
    return verdicts[0][1]


def main() -> int:
    questions = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
    wanted = sys.argv[1:] or sorted(questions)
    s = settings()
    wh = connect(s)
    res = {}
    with Graph(s) as G:
        for qid in wanted:
            refs = references(wh, qid)
            columns = refs[0]["items"]
            tr = trace(G, s, questions[qid]["question"])
            out = {"question": questions[qid]["question"], "compare": columns, "cohort": tr["top"]}
            for route, answer in (("sql", answer_sql), ("cypher", answer_cypher)):
                a = answer(G, s, tr, execute=True, rows=ROWS)
                got = a.get("result")
                if "skipped" in a:
                    verdict, why = "not covered", a["skipped"]
                elif got is None or not got.get("ok", True):
                    failure = (got or {}).get("error") or a.get("error") or a.get("check", {}).get("error")
                    failure = failure or a.get("dry_run", {}).get("error")
                    verdict, why = "failed", str(failure)[:160]
                elif not columns:
                    verdict, why = "not scored", f"{got['total']:,} rows"
                else:
                    verdict, why = judge(refs, got)
                out[route] = {"verdict": verdict, "why": why, "query": a.get("sql") or a.get("cypher")}
                print(f"{qid} {route:6} {verdict:12} {why[:110]}")
            res[qid] = out
    L = ["# Execution accuracy", ""]
    L.append(
        "Each gold question through `qlsc ask`, by both routes, against its reference answer "
        "(`results/answers.md`). **correct** = the same rows on the columns the reference compares; "
        "**not covered** = none of the cohort's tables is in the virtual graph."
    )
    scored = [q for q in res if res[q]["compare"]]
    L += [
        "",
        "| route | correct | wrong | empty | failed | not covered | of scored |",
        "|---|---|---|---|---|---|---|",
    ]
    for route in ROUTES:
        n = lambda v, r=route: sum(1 for q in scored if res[q][r]["verdict"] == v)
        L.append(
            f"| {route} | {n('correct')} | {n('wrong')} | {n('empty')} | {n('failed')} | {n('not covered')} | {len(scored)} |"
        )
    either = sum(1 for q in scored if "correct" in (res[q]["sql"]["verdict"], res[q]["cypher"]["verdict"]))
    L += ["", f"Either route correct (an oracle router's score): {either} of {len(scored)}.", ""]
    L += ["| question | sql | cypher |", "|---|---|---|"]
    for q, r in res.items():
        cell = lambda x: f"{x['verdict']}: {x['why']}".replace("|", "/")
        L.append(f"| {q}. {r['question']} | {cell(r['sql'])} | {cell(r['cypher'])} |")
    print(f"-> {write_result('execution', L, res)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
