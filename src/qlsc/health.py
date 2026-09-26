"""Parse-health report and review sample for a parse run (qlsc/parse.py).

PARSE_HEALTH.md answers "can the graph trust these records?":
- resolution status, split by whether the job succeeded in the warehouse (a query that
  failed there should fail here too);
- an independent check: the warehouse's own referenced tables (base tables, views
  expanded) against the tables the parser resolved, with views expanded through
  the catalog's view definitions;
- what was extracted, and throughput.

REVIEW_SAMPLE.md shows 20 shapes across workloads, SQL beside the extracted record,
for reading by hand.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from qlsc.names import canonical_table, short
from qlsc_parse.catalog import Catalog


def ran_ok(s: dict) -> bool:
    st = s.get("stats")
    return bool(st) and st["jobs"] > st["errors"]


def pct(a, b):
    return f"{a / b:.1%}" if b else "-"


# ---------------------------------------------------------------- cross-check


def crosscheck(shapes, groups, cat) -> tuple[Counter, list]:
    """Parser tables (views expanded) vs the warehouse's referenced tables, per shape."""
    view_src = {}
    for s in shapes:
        if s["origin"] == "catalog_view":
            for w in s["record"].get("writes", []):
                view_src[w["table"]] = {
                    t["id"] for t in s["record"].get("tables", []) if t["id"] != w["table"]
                }

    def base(ts, seen=()):
        out = set()
        for t in ts:
            out |= base(view_src[t], seen + (t,)) if t in view_src and t not in seen else {t}
        return out

    catalog = Catalog(cat)

    def canon(p, d, n):
        return canonical_table(catalog, f"{p}.{d}.{n}")

    ref = {}
    for g in groups:
        if g["jobs"] > g["cache_hits"] and not g["errors"] and g["referenced_tables"]:
            ref.setdefault(
                g["text_id"],
                {
                    canon(x["project_id"], x["dataset_id"], x["table_id"])
                    for x in json.loads(g["referenced_tables"])
                },
            )
    tally, diffs = Counter(), []
    for s in shapes:
        r = s["record"]
        theirs = ref.get(s["sample_text_id"])
        if s["origin"] != "log" or theirs is None or not ran_ok(s):
            continue
        written = {w["table"] for w in r.get("writes", [])}
        st = r.get("statement_type", "?")
        mine = {t["id"] for t in r.get("tables", []) if t["kind"] not in ("system", "transient")}
        if st != "CREATE_VIEW":
            mine -= written
        mine = base(mine)
        # per-run names not in the catalog (Fivetran staging) are transient on both sides
        theirs = {t for t in theirs if "{" not in t or t in cat["tables"]}
        ok = mine == theirs or mine == theirs - written
        tally[(st, ok)] += 1
        if not ok:
            diffs.append((st, sorted(mine - theirs), sorted(theirs - mine), s["sample_sql"][:160]))
    return tally, diffs


# --------------------------------------------------------------------- health


def write(shapes, groups, fps, cat, timing, work: Path):
    log = [s for s in shapes if s["origin"] == "log"]
    okq = [s for s in log if ran_ok(s)]
    bad = [s for s in log if not ran_ok(s)]
    views = [s for s in shapes if s["origin"] == "catalog_view"]
    wh = cat.get("warehouse", "the warehouse")
    L = ["# Parse health", ""]
    w = timing["workers"]
    L += [
        f"Parser `{w['parser']}` ({'compiled' if w.get('compiled') else 'pure Python'}), catalog "
        f"`{cat['version']}`"
        + (f", **sample {timing['sample']:.0%} of distinct texts**" if timing["sample"] else ""),
        "",
    ]
    L += [
        "## Volume",
        "",
        "| | count |",
        "|---|---|",
        f"| Jobs | {timing['jobs']:,} |",
        f"| Log groups (text × principal × week, aggregated in {wh}) | {timing['groups']:,} |",
        f"| Distinct texts (fingerprinted) | {timing['texts']:,} |",
        f"| Shapes from the log (resolved) | {len(log):,} |",
        f"| View definitions from the catalog (resolved) | {len(views):,} |",
        f"| Jobs per shape | {timing['jobs'] / max(len(log), 1):,.0f} |",
        "",
    ]
    fp = timing["fingerprint_server_ms"] / max(timing["fingerprint_items"], 1)
    res = timing["resolve_server_ms"] / max(timing["resolve_items"], 1)
    L += [
        "## Throughput",
        "",
        f"- Fingerprint: {timing['fingerprint_items']:,} texts, {timing['fingerprint_wall_s']:.1f}s wall, "
        f"**{fp:.2f} ms/text** of worker time",
        f"- Resolve: {timing['resolve_items']:,} shapes, {timing['resolve_wall_s']:.1f}s wall, "
        f"**{res:.2f} ms/shape** of worker time",
        "",
    ]

    L += ["## Resolution status", "", "| | ok | partial | error |", "|---|---|---|---|"]
    for name, grp in (
        (f"Ran successfully in {wh}", okq),
        (f"Failed in {wh}", bad),
        ("Catalog view definitions", views),
    ):
        c = Counter(s["record"]["status"] for s in grp)
        L.append(f"| {name} ({len(grp):,}) | {c['ok']:,} | {c['partial']:,} | {c['error']:,} |")
    L.append("")
    L += [
        f"A shape that failed in {wh} is expected to be partial or error here (typos, "
        "missing datasets, denied access all look the same to a parser).",
        "",
    ]

    def misses(grp):
        by = Counter((u["kind"], u["reason"]) for s in grp for u in s["record"].get("unresolved", []))
        names = Counter(
            (u["kind"], u["reason"], u["name"]) for s in grp for u in s["record"].get("unresolved", [])
        )
        return by, names

    by, names = misses(okq + views)
    L += ["### Unresolved references in shapes that ran successfully", ""]
    if by:
        L += ["| kind | reason | occurrences |", "|---|---|---|"]
        L += [f"| {k} | {r} | {n:,} |" for (k, r), n in by.most_common()]
        L += ["", "Top names:", ""] + [f"- `{n}` ({k}, {r}): {c}" for (k, r, n), c in names.most_common(12)]
    else:
        L.append("None.")
    L.append("")
    by, _ = misses(bad)
    L += [
        f"### Unresolved references in shapes that failed in {wh}",
        "",
        "| kind | reason | occurrences |",
        "|---|---|---|",
    ]
    L += [f"| {k} | {r} | {n:,} |" for (k, r), n in by.most_common()]
    errs = Counter(e.split(":")[0] for s in bad for e in s["record"].get("errors", []))
    L += ["", f"Stage errors: {dict(errs) or 'none'}", ""]

    tally, diffs = crosscheck(shapes, groups, cat)
    agree = sum(n for (st, ok), n in tally.items() if ok)
    total = sum(tally.values())
    L += [
        f"## Cross-check against {wh}'s referenced tables",
        "",
        f"For every successful shape whose jobs were not all cache hits: the base tables {wh} "
        f"recorded vs. the tables the parser resolved (views expanded through catalog view SQL).",
        "",
        f"**Agreement: {agree:,} / {total:,} ({pct(agree, total)})**",
        "",
        "| statement | agree | disagree |",
        "|---|---|---|",
    ]
    for st in sorted({st for st, _ in tally}):
        L.append(f"| {st} | {tally[(st, True)]:,} | {tally[(st, False)]:,} |")
    for d in diffs[:10]:
        L += ["", f"- {d[0]}: parser only {d[1]}, {wh} only {d[2]}", f"  `{d[3]}`"]
    L.append("")

    # what was extracted
    T = Counter()
    tables, cols, pairs, jtypes, lin, pf = set(), set(), set(), Counter(), Counter(), Counter()
    for s in okq + views:
        r = s["record"]
        tables |= {
            t["id"] for t in r.get("tables", []) if t["kind"] not in ("system", "transient", "unknown")
        }
        cols |= {(x["table"], x["column"]) for x in r.get("reads", [])}
        for j in r.get("joins", []):
            pairs.add((j["left"]["table"], j["left"]["column"], j["right"]["table"], j["right"]["column"]))
            jtypes[j["type"]] += 1
        for wr in r.get("writes", []):
            for c in wr["columns"]:
                lin[c["kind"]] += 1
        for v in (r.get("scan", {}).get("partition_filter") or {}).values():
            pf[v] += 1
        T["filters"] += len(r.get("filters", []))
        T["star_limit"] += bool(r.get("scan", {}).get("select_star") and r.get("scan", {}).get("limit"))
    ncols = sum(len(t["columns"]) for t in cat["tables"].values())
    L += [
        "## Extracted (successful shapes + view definitions)",
        "",
        f"- Tables referenced: {len(tables):,} of {len(cat['tables']):,} in the catalog ({pct(len(tables), len(cat['tables']))})",
        f"- Columns read: {len(cols):,} of {ncols:,} ({pct(len(cols), ncols)})",
        f"- Distinct column-level join pairs: {len(pairs):,}; join occurrences by type: {dict(jtypes)}",
        f"- Column lineage entries by kind: {dict(lin)}",
        f"- Filter predicates: {T['filters']:,}",
        f"- Partition/shard pruning per table read: {dict(pf)}",
        f"- `SELECT * ... LIMIT` shapes: {T['star_limit']:,}",
        "",
    ]
    unseen = sorted(set(cat["tables"]) - tables)
    L += [
        f"Catalog tables never referenced by any successful shape: {len(unseen)}"
        + (" (sample run: expected to be high)" if timing["sample"] else ""),
        "",
    ]
    L += [f"- `{short(t)}`" for t in unseen[:15]] + (["- ..."] if len(unseen) > 15 else []) + [""]
    (work / "PARSE_HEALTH.md").write_text("\n".join(L))
    review(shapes, fps, work)


# --------------------------------------------------------------------- review

STRATA = [  # (label, n, predicate on (shape, principal, sql))
    (
        "Human ad-hoc SELECT with a join",
        3,
        lambda s, p, q: (
            p == "human" and s["record"].get("joins") and s["record"].get("statement_type") == "SELECT"
        ),
    ),
    ("Human GA4 query (wildcard table, UNNEST)", 1, lambda s, p, q: p == "human" and "events_*" in q),
    (
        "Human SELECT * ... LIMIT",
        1,
        lambda s, p, q: (
            p == "human"
            and s["record"].get("scan", {}).get("select_star")
            and s["record"]["scan"].get("limit")
        ),
    ),
    ("Human query that failed in the warehouse", 1, lambda s, p, q: p == "human" and not ran_ok(s)),
    (
        "Human sandbox CTAS",
        1,
        lambda s, p, q: p == "human" and s["record"].get("statement_type") == "CREATE_TABLE_AS_SELECT",
    ),
    (
        "Looker explore query",
        2,
        lambda s, p, q: (
            p == "looker" and s["record"].get("statement_type") == "SELECT" and "Looker Query Context" in q
        ),
    ),
    (
        "Looker PDT build",
        1,
        lambda s, p, q: p == "looker" and s["record"].get("statement_type") == "CREATE_TABLE_AS_SELECT",
    ),
    ("dbt incremental MERGE", 2, lambda s, p, q: p == "dbt" and s["record"].get("statement_type") == "MERGE"),
    (
        "dbt view (staging or union)",
        2,
        lambda s, p, q: p == "dbt" and s["record"].get("statement_type") == "CREATE_VIEW",
    ),
    (
        "dbt table (CTAS)",
        1,
        lambda s, p, q: p == "dbt" and s["record"].get("statement_type") == "CREATE_TABLE_AS_SELECT",
    ),
    (
        "dbt test or freshness check",
        2,
        lambda s, p, q: p == "dbt" and s["record"].get("statement_type") == "SELECT",
    ),
    ("Data-quality monitor", 1, lambda s, p, q: p == "monitor"),
    ("Fivetran MERGE", 1, lambda s, p, q: p == "fivetran"),
    ("Legacy scheduled INSERT", 1, lambda s, p, q: s["record"].get("statement_type") == "INSERT"),
]


def principal_class(s) -> str:
    """A rough workload class of a shape's main principal, only to pick review examples."""
    top = next(iter((s.get("stats") or {}).get("principals", {})), "") or ""
    for key, cls in (
        ("dbt", "dbt"),
        ("looker", "looker"),
        ("fivetran", "fivetran"),
        ("elementary", "monitor"),
        ("composer", "legacy"),
        ("hightouch", "reverse_etl"),
        ("tableau", "tableau"),
    ):
        if key in top:
            return cls
    return "human" if not top.endswith("gserviceaccount.com") else "service"


def review(shapes, fps, work: Path):
    log = sorted(
        (s for s in shapes if s["origin"] == "log"),
        key=lambda s: hashlib.sha1(s["shape_id"].encode()).hexdigest(),
    )
    picked, used = [], set()
    for label, n, pred in STRATA:
        k = 0
        for s in log:
            if k >= n:
                break
            if s["shape_id"] in used:
                continue
            if ran_ok(s) == ("failed" in label):  # only the failure stratum takes failed shapes
                continue
            try:
                hit = pred(s, principal_class(s), s["sample_sql"])
            except Exception:
                hit = False
            if hit:
                picked.append((label, s))
                used.add(s["shape_id"])
                k += 1
    for s in log:  # top up to 20 if a stratum was empty in this run
        if len(picked) >= 20:
            break
        if s["shape_id"] not in used and ran_ok(s) and s["record"].get("joins"):
            picked.append(("Other successful shape with a join", s))
            used.add(s["shape_id"])
    L = [
        "# Review sample",
        "",
        f"{len(picked)} shapes, chosen deterministically across workloads. For each: the representative SQL, "
        "then what the parser extracted. Literal values are the representative text's own.",
        "",
    ]
    for i, (label, s) in enumerate(picked, 1):
        r, st = s["record"], s["stats"] or {}
        lits = (fps.get(s["sample_text_id"]) or {}).get("literals") or []
        top = ", ".join(f"{p.split('@')[0]} ({n:,})" for p, n in list(st.get("principals", {}).items())[:3])
        L += [
            f"## {i}. {label}",
            "",
            f"`{s['shape_id'][:12]}` · {r.get('statement_type')} · status **{r['status']}** · "
            f"{st.get('jobs', 0):,} jobs ({st.get('errors', 0):,} failed) · {st.get('texts', 0):,} texts · {top}",
            "",
        ]
        sql = s["sample_sql"].strip().splitlines()
        L += (
            ["```sql"]
            + sql[:45]
            + ([f"-- ... ({len(sql) - 45} more lines)"] if len(sql) > 45 else [])
            + ["```", ""]
        )
        tabs = ", ".join(f"`{short(t['id'])}` ({t['kind']})" for t in r.get("tables", []))
        L.append(f"- **Tables:** {tabs or '-'}")
        for j in r.get("joins", []):
            a, b = j["left"], j["right"]
            fmt = lambda x: (
                f"`{short(x['table'])}.{x['column']}{'.' + x['path'] if x['path'] else ''}`"
                + (f" via {x['via']}" if x["via"] not in ("direct", "passthrough") else "")
                + (f" wrapped {x['wrap']}" if x["wrap"] else "")
            )
            L.append(f"- **Join** {j['type']}: {fmt(a)} = {fmt(b)}")
        for wr in r.get("writes", []):
            L.append(f"- **Writes** {wr['mode']} → `{short(wr['table'])}`, {len(wr['columns'])} columns:")
            for c in wr["columns"][:12]:
                src = (
                    ", ".join(
                        f"{short(f['table'])}.{f['column']}{'.' + f['path'] if f.get('path') else ''}"
                        for f in c["from"]
                    )
                    or "-"
                )
                fn = f" {c['fn']}" if c["fn"] else ""
                L.append(f"    - `{c['target']}` ← {src} ({c['kind']}{fn})")
            if len(wr["columns"]) > 12:
                L.append(f"    - ... {len(wr['columns']) - 12} more")
            for k in wr.get("merge_keys", []):
                L.append(
                    f"    - merge key `{k['target']}` ← {', '.join(short(f['table']) + '.' + f['column'] for f in k['from'])}"
                )
        for f in r.get("filters", [])[:10]:
            vals = [lits[i] for i in f["slots"] if i < len(lits)]
            col = f"{short(f['table'])}.{f['column']}{'.' + f['path'] if f['path'] else ''}"
            L.append(f"- **Filter** `{col}` {f['op']} {vals if vals else ''} ({f['clause']}, {f['scope']})")
        sc = r.get("scan", {})
        if sc.get("partition_filter") or sc.get("select_star"):
            L.append(
                f"- **Scan:** partition filter {sc.get('partition_filter')}; select * {sc.get('select_star')}; "
                f"limit {sc.get('limit')}"
            )
        reads = r.get("reads", [])
        rs = "; ".join(
            f"{short(x['table']).split('.')[-1]}.{x['column']}{'.' + x['path'] if x['path'] else ''}"
            f" [{','.join(x['roles'] + [('~' + d) for d in x['derived_roles']])}"
            f"{' ' + '/'.join(x['agg']) if x['agg'] else ''}]"
            for x in reads[:14]
        )
        L.append(f"- **Reads** ({len(reads)}): {rs}{' ...' if len(reads) > 14 else ''}")
        if r.get("unresolved"):
            L.append(
                "- **Unresolved:** "
                + "; ".join(f"{u['kind']} `{u['name']}` ({u['reason']})" for u in r["unresolved"][:6])
            )
        if r.get("errors"):
            L.append(f"- **Errors:** {r['errors']}")
        L.append("")
    (work / "REVIEW_SAMPLE.md").write_text("\n".join(L))
