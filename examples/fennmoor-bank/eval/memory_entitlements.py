"""Memory, phase 2 (plans/2026-09-27-agentic-memory.md, check 4): memory never shows a reader more than
BigQuery, queried as that reader, would.

Anchors:
- customers inside and outside risk's row policy (two in KS or NE, and the two the graph questions name);
- a branch;
- an agent.

The data source remembers every anchor first, so memory holds every row. Then each test principal
(entitlements.principals) remembers and recalls each anchor as themselves (`--as`). For every context
read back from memory:
  1. the same as the principal's own fetch: memory holds what the virtual graph returned them, no more;
  2. the oracle, BigQuery read as the principal directly (not through the gateway, the virtual graph or
     the pass-through):
     - every node is a row they may read, with the same values;
     - every relationship is the foreign key in that row;
     - no property is a column hidden from them, or of a table they can't read (the oracle's allowlist, by
       dry runs as them);
  3. isolation: a customer the principal can't read, remembered by others, is not in their read of memory,
     and recall fetches it (as nothing) instead of serving it; an anchor whose table they can't read is
     refused.
  4. a batch: the customers remembered together, as the principal (qlsc remember Customer KEY... --as), give
     each the context the principal's own fetch of it gave (nothing, for one they can't read), and read
     back from memory the oracle agrees with.
Negative controls: deliberately broken reads of memory the oracle must catch.
  - reads ignored: a row-policied node shown though the reader's own steps never read it;
  - columns unrestricted: the full model's properties;
  - another's reads: read with another principal's steps.

Writes results/memory_entitlements.md and .json.
Usage: uv run examples/fennmoor-bank/eval/memory_entitlements.py
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
from decimal import Decimal

from common import settings, write_result
from entitlements import Oracle
from memory import compare

from qlsc import entitle, memory

NAMED = ["0001000025", "0001000021"]  # the graph questions' customers
INSIDE = ["KS", "NE"]  # risk's row policy (entitlements/setup.py)
BRANCH = 101  # Fennmoor Topeka #101, in KS
CHUNK = 100
BY_CIF = "MATCH (c:Customer) WHERE c.cif_number IN $cifs RETURN c.customer_key AS key"
BY_STATE = """
MATCH (c:Customer) WHERE c.state_code IN $states
RETURN c.customer_key AS key ORDER BY key LIMIT 2
"""
AGENT = """
MATCH (k:Call)-[:HANDLED_BY]->(g:Agent) WHERE k.conversation_date >= $since
RETURN g.agent_user_id AS key, count(k) AS calls ORDER BY calls DESC, key LIMIT 1
"""


def native(v):
    """A value from Neo4j or BigQuery, comparable across the two."""
    v = v.to_native() if hasattr(v, "to_native") else v
    if isinstance(v, Decimal):
        v = float(v)
    if isinstance(v, float):
        return float(f"{v:.9g}")
    if isinstance(v, dt.datetime):  # Virtual Graph returns a TIMESTAMP without its zone: it is UTC
        return (v if v.tzinfo else v.replace(tzinfo=dt.UTC)).astimezone(dt.UTC).isoformat()
    if isinstance(v, dt.date):
        return v.isoformat()
    return v


def literal(v) -> str:
    if isinstance(v, bool) or not isinstance(v, int | str):
        raise TypeError(f"a key the oracle can't write: {v!r}")
    return str(v) if isinstance(v, int) else "'" + v.replace("\\", "\\\\").replace("'", "\\'") + "'"


class Rulebook:
    """What the oracle needs from the virtual graph's model: each label's layer table and columns, and each
    relationship's foreign key in its start's table."""

    def __init__(self, s, m: memory.Model):
        schema = json.loads((s.work / "virtual" / "schema.json").read_text())
        self.table = {label: t["id"] for label, t in m.tables.items()}
        self.column = {
            n["label"]: {p["name"]: p["column"] for p in n["properties"]} for n in schema["entities"]["nodes"]
        }
        self.key = {n["label"]: n["key"][0]["column"] for n in schema["entities"]["nodes"]}
        self.fk = {}
        for r in schema["entities"]["relationships"]:
            start = r["start"]["targetEntity"]
            assert r["table"] == next(n["table"] for n in schema["entities"]["nodes"] if n["label"] == start)
            self.fk[r["label"]] = r["end"]["keys"][0]["relationshipColumn"]


def audit(oracle: Oracle, book: Rulebook, ctx: memory.Context, readable: set, hidden: set) -> list[str]:
    """What memory showed this principal that BigQuery, read as them, doesn't: [] when nothing."""
    out = []
    by_label: dict[str, dict] = {}
    for (label, key), props in ctx.nodes.items():
        by_label.setdefault(label, {})[key] = props
    fks: dict[str, set] = {}
    for ty, start, *_ in ctx.edges:
        fks.setdefault(start, set()).add(book.fk[ty])
    for label, nodes in sorted(by_label.items()):
        table = book.table[label]
        if table not in readable:
            out.append(f"{label}: {len(nodes)} rows of {table}, which they can't read")
            continue
        props = sorted({p for x in nodes.values() for p in x})
        cols = {p: book.column[label][p] for p in props}
        shown = [c for c in cols.values() if (table, c) in hidden]
        if shown:
            out.append(f"{label}: hidden columns shown: {', '.join(sorted(set(shown)))}")
            continue
        key = book.key[label]
        select = sorted(set(cols.values()) | fks.get(label, set()) | {key})
        keys = sorted(nodes, key=str)
        got = {}
        for i in range(0, len(keys), CHUNK):
            part = keys[i : i + CHUNK]
            sql = (
                f"SELECT {', '.join(f'`{c}`' for c in select)} FROM `{table}` "
                f"WHERE `{key}` IN ({', '.join(literal(k) for k in part)})"
            )
            res = oracle.read(sql)
            if "error" in res:
                out.append(f"{label}: their own read of what memory showed fails: {res['error'][:120]}")
                break
            got |= {r[key]: r for r in res["rows"]}
        else:
            missing = [k for k in keys if k not in got]
            if missing:
                out.append(f"{label}: {len(missing)} of {len(keys)} rows they can't read, e.g. {missing[0]}")
            wrong = [
                k
                for k in keys
                if k in got and any(native(v) != native(got[k][cols[p]]) for p, v in nodes[k].items())
            ]
            if wrong:
                out.append(f"{label}: {len(wrong)} rows whose values differ from their read, e.g. {wrong[0]}")
            for ty, start, a, _end, b in ctx.edges:
                if start == label and a in got and native(got[a][book.fk[ty]]) != native(b):
                    out.append(f"{ty}: {a} -> {b}, but their read of {table} has {got[a][book.fk[ty]]}")
                    break
    return out


def main() -> int:
    s = settings()
    principals = s["entitlements"]["principals"]
    now = lambda: dt.datetime.now(dt.UTC)
    ds = memory.reader_model(s, None)
    book = Rulebook(s, ds)
    with memory.virtual_graph(s) as V:
        sign = lambda q: entitle.signing(s, None, q)
        q, e = sign(BY_CIF)
        named = [r["key"] for r in V.rows(q, cifs=NAMED, **e)]
        q, e = sign(BY_STATE)
        inside = [r["key"] for r in V.rows(q, states=INSIDE, **e)]
        q, e = sign(AGENT)
        agent = V.rows(q, since=memory.window_start(s), **e)[0]["key"]
    anchors = [("Customer", k) for k in inside + named] + [("Branch", BRANCH), ("Agent", agent)]
    res: dict = {"anchors": [[a, str(k)] for a, k in anchors], "runs": {}, "isolation": {}, "batch": {},
                 "controls": {}}  # fmt: skip
    alone = {}  # (principal, label, key) -> their own fetch

    for label, key in anchors:  # the data source first: memory holds every row
        ctx = memory.recall(s, label, key, force=True, m=ds)
        print(f"data source: {label} {key}: {len(ctx.nodes)} nodes", flush=True)

    models, oracles, allow = {}, {}, {}
    tables = sorted(book.table.values())
    columns = {
        book.table[label]: sorted(set(c.values())) for label, c in book.column.items() if label in book.table
    }
    for name, who in principals.items():
        models[name] = memory.reader_model(s, name)
        oracles[name] = Oracle(s, who)
        allow[name] = oracles[name].allowlist(tables, columns)
        print(f"{name}: the oracle finds {len(allow[name][0])} of {len(tables)} tables readable, "
              f"{len(allow[name][1])} hidden columns", flush=True)  # fmt: skip

    with memory.memory_graph(s) as M:
        for name, m in models.items():
            run = res["runs"].setdefault(name, {})
            for label, key in anchors:
                entry = run.setdefault(f"{label} {key}", {})
                if label in m.unreadable:
                    entry["verdict"] = "refused"
                    try:
                        memory.recall(s, label, key, m=m)
                        entry["verdict"] = "NOT REFUSED"
                    except memory.Unsupported:
                        pass
                    print(f"{name}: {label} {key}: {entry['verdict']}", flush=True)
                    continue
                fetched = alone[(name, label, key)] = memory.recall(s, label, key, force=True, m=m)
                recalled = memory.recall(s, label, key, m=m)
                if not fetched.nodes:
                    entry |= {"verdict": "nothing they may read", "origin": recalled.origin, "nodes": 0}
                    print(f"{name}: {label} {key}: nothing they may read", flush=True)
                    continue
                diff = (
                    compare(fetched, recalled)
                    if recalled.origin == "memory"
                    else ["recall didn't read memory"]
                )
                incidents = audit(oracles[name], book, recalled, *allow[name])
                entry |= {
                    "nodes": len(recalled.nodes),
                    "edges": len(recalled.edges),
                    "same as their fetch": not diff,
                    "differences": diff,
                    "incidents": incidents,
                    "verdict": "INCIDENT" if incidents else ("ok" if not diff else "DIFFERENT"),
                }
                print(f"{name}: {label} {key}: {len(recalled.nodes)} nodes, {len(recalled.edges)} relationships; "
                      f"{diff or 'same as their fetch'}; "
                      f"{'INCIDENTS: ' + '; '.join(incidents) if incidents else 'the oracle agrees'}", flush=True)  # fmt: skip

        # 4. a batch, as each principal who may read customers
        customers = [k for label, k in anchors if label == "Customer"]
        for name, m in models.items():
            if "Customer" in m.unreadable:
                continue
            batch = memory.recall_batch(s, "Customer", customers, force=True, m=m)
            diffs, incidents = {}, []
            for key in customers:
                own = alone[(name, "Customer", key)]
                d = compare(batch[key], own) if own.nodes or batch[key].nodes else []
                back = memory.recall(s, "Customer", key, m=m)
                if back.nodes:
                    d += (
                        compare(back, batch[key])
                        if back.origin == "memory"
                        else ["recall didn't read memory"]
                    )
                    incidents += audit(oracles[name], book, back, *allow[name])
                if d:
                    diffs[str(key)] = d
            res["batch"][name] = {
                "customers": len(customers),
                "with a context": sum(bool(c.nodes) for c in batch.values()),
                "differences": diffs,
                "incidents": incidents,
                "ok": not diffs and not incidents,
            }
            print(f"batch: {name}: {res['batch'][name]}", flush=True)

        # 3. isolation: a customer risk can't read, remembered by the data source and marketing
        risk = models["risk"]
        outside = next(
            k for k in named if res["runs"]["risk"][f"Customer {k}"]["verdict"] == "nothing they may read"
        )
        direct = memory.run_reads(
            s, risk, memory.template(risk, "Customer", s["memory"]["hops"]), outside, M, True, now()
        )
        res["isolation"]["risk reads memory for a customer others remembered"] = {
            "nodes": len(direct.nodes),
            "ok": not direct.nodes,
        }
        again = memory.recall(s, "Customer", outside, m=risk)
        res["isolation"]["risk's recall of it"] = {"origin": again.origin, "nodes": len(again.nodes),
                                                    "ok": again.origin == "virtual graph" and not again.nodes}  # fmt: skip
        cc = res["runs"]["contact-center"]
        res["isolation"]["contact-center's recall of a customer"] = {
            "ok": all(v["verdict"] == "refused" for k, v in cc.items() if k.startswith("Customer"))
        }
        for k, v in res["isolation"].items():
            print(f"isolation: {k}: {'ok' if v['ok'] else 'FAILED'} {v}", flush=True)

        # negative controls: broken reads of memory, which the oracle must catch
        mk = models["marketing"]
        controls = {
            "reads ignored (risk sees rows its steps never read)": ("risk", dataclasses.replace(risk, policied=set()), [("Customer", outside), ("Branch", BRANCH)]),
            "columns unrestricted (marketing)": ("marketing", dataclasses.replace(ds, reader=mk.reader, allow=mk.allow), [("Customer", named[0])]),
            "another's reads (risk read with marketing's steps)": ("risk", dataclasses.replace(risk, reader=mk.reader), [("Customer", outside)]),
        }  # fmt: skip
        for cname, (name, broken, targets) in controls.items():
            found = []
            for label, key in targets:
                ctx = memory.run_reads(
                    s, broken, memory.template(broken, label, s["memory"]["hops"]), key, M, True, now()
                )
                found += audit(oracles[name], book, ctx, *allow[name]) if ctx.nodes else []
            res["controls"][cname] = {"caught": bool(found), "by": found[:3]}
            print(f"control: {cname}: {'CAUGHT' if found else 'MISSED'} {found[:2]}", flush=True)
    return report(res)


def report(res: dict) -> int:
    rows = [(p, a, x) for p, run in res["runs"].items() for a, x in run.items()]
    incidents = sum(x["verdict"] == "INCIDENT" for _, _, x in rows)
    different = sum(x["verdict"] == "DIFFERENT" for _, _, x in rows)
    L = [
        "# Memory's entitlements, with the warehouse as the oracle",
        "",
        "Check 4 of plans/2026-09-27-agentic-memory.md (phase 2): memory never shows a reader more than "
        "BigQuery, queried as that reader, would. The data source remembers every anchor first, so memory "
        "holds every row; each principal then remembers and recalls them as themselves (`--as`). Every "
        "context read back from memory is checked against BigQuery read as the principal directly: each node "
        "a row they may read, with the same values; each relationship the foreign key in that row; no hidden "
        "column; no table they can't read.",
        "",
        f"**{incidents} incidents** in {len(rows)} recalls; {different} differed from the principal's own fetch.",
        "",
        "| principal | anchor | nodes | relationships | same as their fetch | verdict |",
        "|---|---|---|---|---|---|",
    ]
    for p, a, x in rows:
        same = "" if "same as their fetch" not in x else ("yes" if x["same as their fetch"] else "**no**")
        L.append(f"| {p} | {a} | {x.get('nodes', '')} | {x.get('edges', '')} | {same} | {x['verdict']} |")
    L += ["", "## Isolation", "", "| check | result |", "|---|---|"]
    L += [f"| {k} | {'ok' if v['ok'] else '**FAILED**'} |" for k, v in res["isolation"].items()]
    L += ["", "## A batch", "", "The customers remembered together, as each principal who may read them.", ""]
    L += [
        "| principal | customers | with a context | same as their own fetches | the oracle |",
        "|---|---|---|---|---|",
    ]
    L += [
        f"| {k} | {v['customers']} | {v['with a context']} | {'yes' if not v['differences'] else '**no**'} "
        f"| {'agrees' if not v['incidents'] else '**' + str(len(v['incidents'])) + ' incidents**'} |"
        for k, v in res["batch"].items()
    ]
    L += [
        "",
        "## Negative controls: broken reads of memory the oracle must catch",
        "",
        "| broken read | caught | by |",
        "|---|---|---|",
    ]
    L += [
        f"| {k} | {'yes' if v['caught'] else '**NO**'} | {'; '.join(v['by'][:1])} |"
        for k, v in res["controls"].items()
    ]
    print(f"-> {write_result('memory_entitlements', L, res)}")
    ok = not incidents and not different and all(v["ok"] for v in res["isolation"].values())
    ok = (
        ok
        and all(v["caught"] for v in res["controls"].values())
        and all(v["ok"] for v in res["batch"].values())
    )
    ok = ok and not any(x["verdict"] == "NOT REFUSED" for _, _, x in rows)
    print("all checks passed" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
