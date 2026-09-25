"""Stage 7b: the semantic layer as tools an agent (or a person) can call.

Every tool reads the graph the earlier stages built, and dry_run reads BigQuery's
planner. They return compact JSON, sized for a model's context. The same functions
could back an MCP server; pipeline/answer.py drives them with an LLM.

  search_tables(query)          meaning + usage retrieval (pipeline/retrieve.py), each hit with
                                its status and why
  find_tables_by_name(pattern)  names, for questions about names
  describe_table(table)         what it is, whether to use it, its columns and their variables,
                                how the business filters and joins it, where it comes from
  join_path(tables)             how to join a set of tables, from joins the business runs
  find_columns(query)           variables (and their columns) by meaning or name
  column_detail(column)         a column's variable, lineage and the values filtered on
  dry_run(sql)                  BigQuery's verdict on the SQL, plus the status of what it reads

A catalog-only baseline (what an agent gets from INFORMATION_SCHEMA alone) is
CatalogTools: names, columns, types, partitioning and dry_run - no usage.
"""
from __future__ import annotations

import fnmatch
import heapq
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from graphdb import Graph, config

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
CONF_WEIGHT = {"production": 1.0, "corroborated": 1.3, "single": 1.8}
SHARED_VAR_WEIGHT = 2.5          # never joined on directly, but the same variable on both sides
AVOID_PENALTY = 4.0


def short(x: str) -> str:
    return x.split(".", 1)[1] if x.count(".") >= 2 else x


def clip(s: str | None, n: int) -> str | None:
    if not s:
        return s
    return s if len(s) <= n else s[:n - 3] + "..."


class Physical:
    """Logical names (what the log and the graph use) -> the deployed BigQuery tables."""

    def __init__(self, G: Graph, cfg: dict):
        cat = json.loads((WORK / "catalog.json").read_text())
        self.ds = {logical: phys for phys, logical in cat["aliases"].items()}
        self.by_dataset = {logical.split(".", 1)[1]: logical for logical in self.ds}
        self.phys_name = {}
        for r in G.rows("MATCH (t:Table) WHERE t.in_catalog RETURN t.id AS t, t.physical_names AS p, t.kind AS k"):
            if r["p"] and r["k"] != "wildcard":
                self.phys_name[r["t"]] = sorted(r["p"])[-1]

    def logical(self, text: str) -> str:
        """Deployed names back to the estate's own (catalog view definitions carry the deployed ones)."""
        for logical, phys in sorted(self.ds.items(), key=lambda x: -len(x[1])):
            text = text.replace(phys + ".", logical + ".")
        return text

    def rewrite(self, sql: str) -> str:
        import sqlglot
        from sqlglot import exp
        tree = sqlglot.parse_one(sql, read="bigquery")
        ctes = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
        for t in tree.find_all(exp.Table):
            name, db, proj = t.name, t.db, t.catalog
            if not db:
                continue
            logical = f"{proj}.{db}" if proj else self.by_dataset.get(db)
            if not logical or logical not in self.ds:
                continue
            p_proj, p_ds = self.ds[logical].split(".", 1)
            name = self.phys_name.get(f"{logical}.{name}", name)
            t.set("catalog", exp.to_identifier(p_proj))
            t.set("db", exp.to_identifier(p_ds))
            t.set("this", exp.to_identifier(name))
        return tree.sql(dialect="bigquery")


class BigQueryDryRun:
    def __init__(self, cfg: dict):
        from extract import client
        self.c = client(cfg)

    def __call__(self, sql: str) -> dict:
        from google.cloud import bigquery
        try:
            job = self.c.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
            return {"ok": True, "bytes_processed": job.total_bytes_processed}
        except Exception as e:                  # the planner's message is the useful part
            msg = getattr(e, "message", None) or str(e)
            msg = re.sub(r"^POST https://\S+: ", "", re.sub(r"jeffdavis-bq-testproj[:.]fnb_", "", msg))
            return {"ok": False, "error": clip(msg.split("\n")[0], 400)}


class SemanticTools:
    def __init__(self, G: Graph | None = None, cfg: dict | None = None, bq: bool = True):
        self.cfg = cfg or config()
        self.G = G or Graph(self.cfg)
        self._emb = None
        self.T = {r["t"]["id"]: r["t"] for r in self.G.rows("""MATCH (t:Table)-[:IN_DATASET]->(d:Dataset) WHERE t.in_catalog
            RETURN t {.id, .name, .kind, .layer, .status, .status_reasons, .freshness, .display_name, .description,
                      .consumer_count, .partition_column, .cluster_columns, restricted: d.restricted} AS t""")}
        self.alt = defaultdict(list)
        for r in self.G.rows("MATCH (a:Table)-[u:USE_INSTEAD]->(b:Table) RETURN a.id AS a, b.id AS b, u.why AS why"):
            self.alt[r["a"]].append({"table": r["b"], "why": r["why"]})
        self.phys = Physical(self.G, self.cfg)
        self.dry = BigQueryDryRun(self.cfg) if bq else None

    # ------------------------------------------------------------ helpers
    @property
    def emb(self):
        if self._emb is None:
            from semantics import Embedder
            self._emb = Embedder(self.cfg)
        return self._emb

    def resolve(self, name: str) -> str | None:
        name = name.strip().strip("`")
        if name in self.T:
            return name
        low = name.lower()
        hits = [t for t in self.T if t.lower() == low or short(t).lower() == low or t.lower().endswith("." + low)]
        if not hits:           # a physical Looker PDT or a date shard
            hits = [t for t in self.T if re.fullmatch(re.escape(t.lower()).replace(r"\{id\}", "[0-9a-z]+")
                                                      .replace(r"\*", r"\d+"), low) or
                    re.fullmatch(re.escape(short(t).lower()).replace(r"\{id\}", "[0-9a-z]+").replace(r"\*", r"\d+"), low)]
        return hits[0] if len(hits) == 1 else None

    def brief(self, t: str) -> dict:
        m = self.T[t]
        out = {"table": t, "name": m.get("display_name"), "what": clip(m.get("description"), 220),
               "status": m.get("status"), "used_by": m.get("consumer_count") or 0}
        if m.get("status") != "current" and m.get("status_reasons"):
            out["why"] = clip(" ".join(m["status_reasons"]), 300)
        if self.alt.get(t):
            out["use_instead"] = [a["table"] for a in self.alt[t]]
        return out

    def coverage(self, t: str) -> str | None:
        """Date coverage a catalog name reveals: the first and last shard of a sharded table."""
        r = self.G.rows("MATCH (t:Table {id: $t}) RETURN t.physical_names AS p, t.kind AS k", t=t)
        p = sorted(r[0]["p"] or []) if r else []
        if r and r[0]["k"] == "wildcard" and p:
            suf = [re.search(r"(\d{6,8})$", x) for x in p]
            suf = [m.group(1) for m in suf if m]
            if suf:
                return f"{len(p)} date shards, {suf[0]} to {suf[-1]}"
        return None

    def sources(self, t: str) -> list[str]:
        """The tables its data ultimately comes from, with any date coverage their names reveal."""
        rows = self.G.rows("""MATCH (t:Table {id: $t})-[:DERIVED_FROM*1..8]->(r:Table)
            WHERE NOT (r)-[:DERIVED_FROM]->(:Table {in_catalog: true}) AND r.in_catalog
            RETURN DISTINCT r.id AS r""", t=t)
        out = []
        for r in sorted(x["r"] for x in rows):
            cov = self.coverage(r)
            out.append(r + (f" ({cov})" if cov else "") + (f" [{self.T[r]['status']}]" if r in self.T and self.T[r]["status"] == "avoid" else ""))
        return out[:15]

    # ------------------------------------------------------------ tools
    def example_queries(self, tables: list[str], k: int = 4) -> dict:
        ids = [self.resolve(t) for t in tables]
        if not all(ids):
            return {"error": f"unknown tables: {[t for t, i in zip(tables, ids) if not i]}"}
        rows = self.G.rows("""MATCH (s:QueryShape {succeeded: true})-[:REFERENCES]->(t:Table) WHERE t.id IN $ids
              AND s.purpose IN ['bi', 'build', 'adhoc', 'extract', 'ml_read']
            WITH s, count(DISTINCT t) AS hit WHERE hit >= $need
            OPTIONAL MATCH (p:Principal)-[r:RAN]->(s)
            WITH s, hit, count(DISTINCT p) AS people, max(r.last_seen) AS last
            OPTIONAL MATCH (s)-[:USES_JOIN]->(bad:JoinKey {confidence: 'suspect'})
            OPTIONAL MATCH (s)-[:REFERENCES]->(x:Table {status: 'avoid'})
            OPTIONAL MATCH (s)-[:WRITES]->(w:Table)
            RETURN s.id AS id, s.family_id AS fam, s.purpose AS purpose, split(s.author, ':')[0] AS who, s.jobs AS jobs,
                   hit, people, substring(last, 0, 10) AS last, count(DISTINCT bad) AS suspect,
                   collect(DISTINCT x.id) AS avoid, collect(DISTINCT w.id) AS writes, s.sample_sql AS q""",
                           ids=ids, need=len(ids) if len(ids) <= 2 else max(2, len(ids) - 1))
        rows = [r for r in rows if not r["suspect"]]
        rows.sort(key=lambda r: (-r["hit"], bool(r["avoid"]), r["who"] == "person", -r["people"], -r["jobs"]))
        out, fams = [], set()
        for r in rows:
            if r["fam"] in fams:
                continue
            fams.add(r["fam"])
            head = (f"-- {r['purpose']} by {'people' if r['who'] == 'person' else r['who']}: {r['jobs']} runs by "
                    f"{r['people']} principal(s), last {r['last']}"
                    + (f"; writes {', '.join(short(w) for w in r['writes'])}" if r["writes"] else "")
                    + (f"; reads avoid-status {', '.join(short(a) for a in r['avoid'])}" if r["avoid"] else ""))
            out.append(head + "\n" + clip(self.phys.logical(r["q"]), 1500))
            if len(out) >= k:
                break
        return {"queries": out} if out else {"queries": [], "note": "no successful query in the log reads these tables together"}

    def sensitive_data(self) -> dict:
        rows = self.G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) WHERE t.in_catalog AND (c.sensitive OR c.hashed)
            MATCH (t)-[:IN_DATASET]->(d:Dataset)
            OPTIONAL MATCH (f:Finding)-[:ABOUT]->(x) WHERE (x = c OR x = t) AND f.kind IN ['pii_exposure', 'pii_candidate']
            RETURN t.id AS t, t.status AS st, d.restricted AS restricted, c.name AS c, c.sensitive AS s, c.hashed AS h,
                   c.hash_evidence AS how, collect(DISTINCT f.title) AS f ORDER BY t.id""")
        by = defaultdict(lambda: {"columns": [], "findings": set()})
        for r in rows:
            b = by[r["t"]]
            b["status"], b["restricted_dataset"] = r["st"], bool(r["restricted"])
            b["columns"].append(f"{r['c']}: " + ("hashed" + (" (seen hashed in lineage)" if r["how"] == "lineage" else
                                                          " (named as a hash)") if r["h"] else "RAW value"))
            b["findings"] |= set(r["f"])
        return {"how": "Sensitive = production hashes it somewhere, it sits in a dataset people are denied, or it is "
                       "named like an SSN / tax id. Hashed = the output of SHA256/MD5 in lineage, or named as a hash.",
                "tables": [{"table": t, **{k: (sorted(v) if isinstance(v, set) else v) for k, v in b.items()}}
                           for t, b in by.items()]}

    def search_tables(self, query: str, k: int = 8) -> dict:
        from retrieve import search
        hits = search(query, k, self.G, self.emb)
        return {"results": [self.brief(h["table"]) | {"matched_by": h["why"][:2]} for h in hits if h["table"] in self.T]}

    def find_tables_by_name(self, pattern: str) -> dict:
        pat = pattern.strip().strip("`")
        glob = pat if any(ch in pat for ch in "*?[") else f"*{pat}*"
        hits = [t for t in self.T if fnmatch.fnmatch(self.T[t]["name"].lower(), glob.lower())
                or fnmatch.fnmatch(short(t).lower(), glob.lower())]
        hits.sort(key=short)
        return {"pattern": glob, "matches": len(hits), "results": [self.brief(t) for t in hits[:40]]}

    def describe_table(self, table: str) -> dict:
        t = self.resolve(table)
        if not t:
            return {"error": f"no table named {table}; use search_tables or find_tables_by_name"}
        G, m = self.G, self.T[t]
        full = G.rows("MATCH (t:Table {id: $t}) RETURN t.abbreviations AS a", t=t)[0]
        cols = G.rows("""MATCH (t:Table {id: $t})-[:HAS_COLUMN]->(c:Column) WHERE c.in_catalog
            OPTIONAL MATCH (c)-[:IS]->(v:Variable)
            OPTIONAL MATCH (f:Finding)-[:ABOUT]->(c)
            RETURN c.name AS c, c.type AS type, v.display_name AS var, v.role AS role, v.hub AS hub, v.tables AS vt,
                   c.sensitive AS sensitive, c.hashed AS hashed, collect(DISTINCT f.kind) AS findings""", t=t)
        colout = []
        for c in cols[:70]:
            s = f"{c['c']} {c['type'] or ''}"
            bits = []
            if c["var"]:
                bits.append(f"{c['var']}" + (f", {c['role']}" if c["role"] else "") +
                            (", estate-wide key" if c["hub"] else "") + (f", in {c['vt']} tables" if (c["vt"] or 0) > 1 else ""))
            if c["sensitive"]:
                bits.append("SENSITIVE" + (" (stored hashed)" if c["hashed"] else " (raw value)"))
            elif c["hashed"]:
                bits.append("stored hashed")
            bits += [f"finding: {k}" for k in c["findings"] if k]
            colout.append(s + (f" [{'; '.join(bits)}]" if bits else ""))
        src = G.rows("""MATCH (t:Table {id: $t})-[d:DERIVED_FROM]->(s:Table) RETURN s.id AS s, s.status AS st, s.display_name AS n
                        ORDER BY s.id""", t=t)
        feeds = G.rows("""MATCH (t:Table {id: $t})<-[:DERIVED_FROM]-(x:Table) RETURN x.id AS d, x.status AS st,
                          x.display_name AS n, x.description AS what ORDER BY x.consumer_count DESC LIMIT 6""", t=t)
        # how the business filters it: most-run filters, by who; values seen on those columns
        filt = G.rows("""MATCH (t:Table {id: $t})-[:HAS_COLUMN]->(c:Column)<-[f:FILTERS]-(s:QueryShape {succeeded: true})
            WHERE s.purpose IN ['adhoc', 'bi', 'build', 'extract', 'ml_read']
            WITH c, f.op AS op, CASE WHEN split(s.author, ':')[0] = 'person' THEN 'people' ELSE 'production/BI' END AS who,
                 sum(s.jobs) AS jobs
            RETURN c.name AS c, op, who, jobs ORDER BY jobs DESC LIMIT 12""", t=t)
        vals = {r["c"]: r["v"] for r in G.rows("""MATCH (t:Table {id: $t})-[:HAS_COLUMN]->(c:Column)-[h:HAS_VALUE]->(l:Literal)
            WITH c, l, h ORDER BY h.jobs DESC
            RETURN c.name AS c, collect(l.value + ' (' + toString(h.jobs) + ' jobs, ' + substring(h.first_seen, 0, 10) + '..' +
                   substring(h.last_seen, 0, 10) + ')')[..6] AS v""", t=t)}
        filters = []
        for f in filt:
            s = f"{f['c']} {f['op']} - {f['who']}, {f['jobs']} jobs"
            filters.append(s)
        joins = G.rows("""MATCH (t:Table {id: $t})-[j:JOINS]-(o:Table) RETURN o.id AS o, o.status AS st, j.on AS on,
                          j.confidence AS conf, j.suspect AS suspect, j.shapes AS shapes ORDER BY j.shapes DESC LIMIT 10""", t=t)
        who = G.rows("""MATCH (p:Principal)-[c:CONSUMES]->(t:Table {id: $t})
                        RETURN p.class AS cls, count(*) AS n, sum(c.jobs) AS jobs ORDER BY jobs DESC""", t=t)
        fnd = G.rows("""MATCH (f:Finding)-[a:ABOUT]->(x) WHERE x.id = $t OR x.id STARTS WITH $t + '.'
                        RETURN DISTINCT f.kind AS kind, a.role AS role, f.title AS title, f.summary AS summary""", t=t)
        build = G.rows("""MATCH (s:QueryShape {succeeded: true})-[:WRITES]->(t:Table {id: $t})
            WHERE s.purpose IN ['build', 'view_definition']
            RETURN split(s.author, ':')[0] AS who, s.jobs AS jobs, s.sample_sql AS q ORDER BY s.last_seen DESC LIMIT 1""", t=t)
        sample = G.rows("""MATCH (s:QueryShape {succeeded: true})-[:REFERENCES]->(t:Table {id: $t})
            WHERE s.purpose IN ['bi', 'extract', 'ml_read'] OR (s.purpose = 'build' AND NOT (s)-[:WRITES]->(t))
            RETURN s.purpose AS p, split(s.author, ':')[0] AS who, s.jobs AS jobs, s.sample_sql AS q
            ORDER BY s.jobs DESC LIMIT 1""", t=t)
        out = {"table": t, "name": m.get("display_name"), "description": m.get("description"),
               "abbreviations": json.loads(full["a"] or "[]"),
               "kind": m["kind"], "layer": m.get("layer"), "status": m.get("status"),
               "status_reasons": m.get("status_reasons") or [], "freshness": m.get("freshness"),
               "use_instead": self.alt.get(t, []), "restricted_dataset": bool(m.get("restricted")),
               "partition_column": m.get("partition_column"), "cluster_columns": m.get("cluster_columns") or [],
               "columns": colout + ([f"... {len(cols) - 70} more"] if len(cols) > 70 else []),
               "built_from": [f"{s['s']} ({s['st'] or 'not in catalog'})" for s in src][:12],
               "feeds": [f"{d['d']} ({d['st']}): {d['n']} - {clip(d['what'], 160)}" for d in feeds],
               "filtered_on": filters, "values_filtered_on": vals,
               "joined_with": [f"{j['o']} on {', '.join(j['on'][:3])} ({j['shapes']} queries)" +
                               (" - includes a SUSPECT key, do not use that one" if j["suspect"] else "") +
                               (f" [{j['st']}]" if j["st"] != "current" else "") for j in joins],
               "used_by": {r["cls"]: r["n"] for r in who},
               "findings": [f"{f['kind']} ({f['role']}): {f['title']} - {clip(f['summary'], 400)}" for f in fnd][:8],
               "sources": self.sources(t),
               "build_sql": [(f"-- how it is built ({b['who']}, {b['jobs']} runs)" if b["who"] else "-- view definition")
                             + f"\n{clip(self.phys.logical(b['q']), 1800)}" for b in build],
               "sample_sql": [f"-- {s['who']} {s['p']}, {s['jobs']} runs\n{clip(s['q'], 900)}" for s in sample],
               "more": "example_queries shows how people and production query it"}
        return out

    def join_path(self, tables: list[str]) -> dict:
        ids = [self.resolve(t) for t in tables]
        missing = [t for t, i in zip(tables, ids) if not i]
        if missing:
            return {"error": f"unknown tables: {missing}"}
        G = self.G
        # observed joins, column level
        edges = defaultdict(list)
        for r in G.rows("""MATCH (t1:Table)-[:HAS_COLUMN]->(a:Column)<-[:ON {side: 'left'}]-(k:JoinKey)-[:ON {side: 'right'}]->(b:Column)
                                 <-[:HAS_COLUMN]-(t2:Table)
                           WHERE t1 <> t2 AND t1.in_catalog AND t2.in_catalog AND k.confidence IN ['production', 'corroborated', 'single']
                           OPTIONAL MATCH (s:QueryShape)-[u:USES_JOIN]->(k)
                           RETURN t1.id AS t1, t2.id AS t2, a.name AS a, b.name AS b, k.confidence AS conf, k.people AS people,
                                  count(s) AS shapes, collect(u.left_wrap + u.right_wrap)[..3] AS wraps"""):
            wraps = sorted({w for ws in r["wraps"] for w in (ws or [])})
            e = {"on": f"{short(r['t1'])}.{r['a']} = {short(r['t2'])}.{r['b']}", "evidence": f"{r['conf']} join, "
                 f"{r['shapes']} queries" + (f", written with {'/'.join(wraps)}" if wraps else ""), "w": CONF_WEIGHT[r["conf"]]}
            edges[(r["t1"], r["t2"])].append(e)
            edges[(r["t2"], r["t1"])].append({**e, "on": f"{short(r['t2'])}.{r['b']} = {short(r['t1'])}.{r['a']}"})
        # shared identifier variables (never joined directly, but the same thing on both sides)
        by_var = defaultdict(list)
        for r in G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)-[:IS]->(v:Variable {role: 'identifier'})
                           WHERE t.in_catalog AND c.in_catalog AND v.tables >= 2
                           RETURN v.id AS v, v.display_name AS vn, t.id AS t, c.name AS c, c.type AS type"""):
            by_var[r["v"]].append(r)
        for v, rs in by_var.items():
            if len(rs) > 60:
                continue
            for x in rs:
                for y in rs:
                    if x["t"] != y["t"] and not edges.get((x["t"], y["t"])):
                        edges[(x["t"], y["t"])].append({
                            "on": f"{short(x['t'])}.{x['c']} = {short(y['t'])}.{y['c']}",
                            "evidence": f"same variable ({x['vn']}) on both sides; nobody joins these two tables directly"
                                        + (f"; types differ ({x['type']} vs {y['type']}): cast" if x["type"] != y["type"] else ""),
                            "w": SHARED_VAR_WEIGHT, "inferred": True})
        adj = defaultdict(dict)
        for (a, b), es in edges.items():
            best = min(es, key=lambda e: e["w"])
            w = best["w"] + (AVOID_PENALTY if self.T.get(b, {}).get("status") == "avoid" else 0)
            adj[a][b] = (w, es)

        def dijkstra(srcs: set[str]):
            dist, prev, pq = {s: 0.0 for s in srcs}, {}, [(0.0, s) for s in srcs]
            while pq:
                d, u = heapq.heappop(pq)
                if d > dist.get(u, math.inf):
                    continue
                for v, (w, _) in adj[u].items():
                    if d + w < dist.get(v, math.inf):
                        dist[v], prev[v] = d + w, u
                        heapq.heappush(pq, (d + w, v))
            return dist, prev
        tree, steps, unreached = {ids[0]}, [], []
        for t in ids[1:]:
            if t in tree:
                continue
            dist, prev = dijkstra(tree)
            if t not in dist:
                unreached.append(t)
                continue
            path, cur = [], t
            while cur not in tree:
                path.append((prev[cur], cur))
                cur = prev[cur]
            for a, b in reversed(path):
                es = sorted(adj[a][b][1], key=lambda e: e["w"])
                steps.append({"from": a, "to": b, "join_on": [e["on"] for e in es[:3] if e["w"] == es[0]["w"]],
                              "evidence": es[0]["evidence"],
                              **({"via_status": self.T[b]["status"]} if b not in ids and self.T[b]["status"] != "current" else {})})
                tree.add(b)
        bad = G.rows("""MATCH (t1:Table)-[:HAS_COLUMN]->(a:Column)<-[:ON]-(k:JoinKey {confidence: 'suspect'})-[:ON]->(b:Column)<-[:HAS_COLUMN]-(t2:Table)
                        WHERE t1.id IN $ids AND t1 <> t2
                        RETURN DISTINCT a.id AS a, b.id AS b, k.confidence_reason AS why""", ids=[i for i in ids if i])
        out = {"steps": steps, "through": sorted(tree - set(ids))}
        if unreached:
            out["unreached"] = [f"{t}: no join or shared key connects it to the others in the log" for t in unreached]
        if bad:
            out["do_not_join"] = [f"{short(b['a'])} = {short(b['b'])}: {b['why']}" for b in bad]
        return out

    def find_columns(self, query: str, k: int = 8) -> dict:
        from retrieve import centered
        vec = centered(self.G, self.emb.embed([query])[0], "Variable")
        rows = self.G.rows("""CALL db.index.vector.queryNodes('variable_embedding', $k, $v) YIELD node, score
            MATCH (node)<-[:IS]-(c:Column)<-[:HAS_COLUMN]-(t:Table) WHERE t.in_catalog
            WITH node, score, collect(DISTINCT t.id + '.' + c.name + CASE WHEN c.sensitive THEN
                 CASE WHEN c.hashed THEN ' [sensitive, hashed]' ELSE ' [sensitive, RAW]' END ELSE '' END +
                 ' (' + coalesce(t.status, '?') + ')') AS cols
            RETURN node.display_name AS name, node.role AS role, node.description AS d, score, cols ORDER BY score DESC""",
                           k=k, v=vec)
        words = [w for w in re.split(r"\W+", query.lower()) if len(w) >= 3]
        by_name = self.G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) WHERE t.in_catalog AND c.in_catalog
            AND any(w IN $w WHERE toLower(c.name) CONTAINS w)
            RETURN t.id + '.' + c.name + CASE WHEN c.sensitive THEN CASE WHEN c.hashed THEN ' [sensitive, hashed]'
                   ELSE ' [sensitive, RAW]' END ELSE '' END + ' (' + coalesce(t.status, '?') + ')' AS c LIMIT 40""", w=words)
        return {"variables": [{"variable": r["name"], "role": r["role"], "what": clip(r["d"], 200),
                               "columns": r["cols"][:15]} for r in rows],
                "columns_named_like": [r["c"] for r in by_name]}

    def column_detail(self, column: str) -> dict:
        tname, _, cname = column.strip().strip("`").rpartition(".")
        t = self.resolve(tname)
        if not t:
            return {"error": f"no table {tname}"}
        G = self.G
        r = G.rows("""MATCH (t:Table {id: $t})-[:HAS_COLUMN]->(c:Column) WHERE toLower(c.name) = toLower($c)
            OPTIONAL MATCH (c)-[:IS]->(v:Variable)
            RETURN c.id AS id, c.name AS name, c.type AS type, c.sensitive AS s, c.hashed AS h, v.display_name AS var,
                   v.description AS vd, v.role AS role""", t=t, c=cname)
        if not r:
            return {"error": f"{t} has no column {cname}"}
        c = r[0]
        up = G.rows("""MATCH p = (src:Column)-[:FLOWS*1..3]->(c:Column {id: $c})
            WITH p, [r IN relationships(p) | coalesce(r.fns, [])] AS fns, [r IN relationships(p) | r.kinds] AS kinds
            RETURN [n IN nodes(p) | n.id] AS path, fns, kinds LIMIT 12""", c=c["id"])
        vals = G.rows("""MATCH (c:Column {id: $c})-[h:HAS_VALUE]->(l:Literal)
            RETURN l.value AS v, h.op AS op, h.jobs AS jobs, substring(h.first_seen, 0, 10) AS first,
                   substring(h.last_seen, 0, 10) AS last ORDER BY h.jobs DESC LIMIT 20""", c=c["id"])
        fnd = G.rows("MATCH (f:Finding)-[:ABOUT]->(:Column {id: $c}) RETURN f.title + ': ' + f.summary AS f", c=c["id"])
        return {"column": c["id"], "type": c["type"], "variable": c["var"], "role": c["role"], "what": clip(c["vd"], 300),
                "sensitive": bool(c["s"]), "hashed": bool(c["h"]),
                "comes_from": [" <- ".join(short(x) for x in reversed(u["path"])) +
                               (f" (via {', '.join(sorted({f for fs in u['fns'] for f in fs}))})" if any(u["fns"]) else "")
                               for u in up],
                "values_filtered_on": [f"{v['op']} {v['v']}: {v['jobs']} jobs, {v['first']}..{v['last']}" for v in vals],
                "findings": [clip(f["f"], 500) for f in fnd]}

    def dry_run(self, sql: str) -> dict:
        import sqlglot
        from sqlglot import exp
        try:
            tree = sqlglot.parse_one(sql, read="bigquery")
        except Exception as e:
            return {"ok": False, "error": f"parse error: {clip(str(e), 300)}"}
        ctes = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
        read, notes = set(), []
        for tb in tree.find_all(exp.Table):
            if tb.name.lower() in ctes and not tb.db:
                continue
            ref = ".".join(p for p in (tb.catalog, tb.db, tb.name) if p)
            t = self.resolve(ref)
            if t:
                read.add(t)
        for t in sorted(read):
            if self.T[t].get("status") == "avoid":
                notes.append(f"reads {t}, status avoid: {clip(' '.join(self.T[t]['status_reasons']), 250)}")
        res = self.dry(self.phys.rewrite(sql)) if self.dry else {"ok": None, "error": "dry run disabled"}
        return res | {"reads": sorted(read), **({"warnings": notes} if notes else {})}


class CatalogTools:
    """Baseline: what an agent gets from INFORMATION_SCHEMA alone - no usage, no findings."""

    def __init__(self, G: Graph | None = None, cfg: dict | None = None, bq: bool = True):
        self.cfg = cfg or config()
        G = G or Graph(self.cfg)
        cat = json.loads((WORK / "catalog.json").read_text())
        tables = cat["tables"] if isinstance(cat["tables"], dict) else dict(cat["tables"])
        self.T = tables
        self.phys = Physical(G, self.cfg)
        self.dry = BigQueryDryRun(self.cfg) if bq else None

    def resolve(self, name: str) -> str | None:
        name = name.strip().strip("`").lower()
        hits = [t for t in self.T if t.lower() == name or short(t).lower() == name]
        return hits[0] if len(hits) == 1 else None

    def list_tables(self, pattern: str = "*") -> dict:
        glob = pattern if any(ch in pattern for ch in "*?[") else f"*{pattern}*"
        hits = sorted(t for t in self.T if fnmatch.fnmatch(t.lower(), glob.lower())
                      or fnmatch.fnmatch(t.rsplit(".", 1)[-1].lower(), glob.lower())
                      or fnmatch.fnmatch(short(t).lower(), glob.lower()))
        return {"matches": len(hits), "tables": [f"{t} ({self.T[t].get('kind', '').lower()})" for t in hits[:400]]}

    def table_schema(self, table: str) -> dict:
        t = self.resolve(table)
        if not t:
            return {"error": f"no table named {table}"}
        m = self.T[t]
        return {"table": t, "kind": m.get("kind"), "partition_column": m.get("partition"),
                "cluster_columns": m.get("cluster") or [], "columns": [f"{c} {ty}" for c, ty in m["columns"].items()]}

    def search_columns(self, pattern: str) -> dict:
        glob = pattern if any(ch in pattern for ch in "*?[") else f"*{pattern}*"
        hits = [f"{t}.{c} {ty}" for t, m in self.T.items() for c, ty in m["columns"].items()
                if fnmatch.fnmatch(c.lower(), glob.lower())]
        return {"matches": len(hits), "columns": hits[:80]}

    def dry_run(self, sql: str) -> dict:
        try:
            return self.dry(self.phys.rewrite(sql)) if self.dry else {"ok": None}
        except Exception as e:
            return {"ok": False, "error": f"parse error: {clip(str(e), 300)}"}


def schema(name: str, desc: str, props: dict, required: list[str]) -> dict:
    return {"name": name, "description": desc,
            "input_schema": {"type": "object", "properties": props, "required": required}}


S = {"type": "string"}
SEMANTIC_TOOLS = [
    schema("example_queries", "SQL the business already runs against these tables (production models, BI, "
           "and people), ranked by how many principals run it; queries through wrong joins are left out. Use "
           "it to reuse the business's own definitions: denominators, flags, date logic, code mappings.",
           {"tables": {"type": "array", "items": S}}, ["tables"]),
    schema("sensitive_data", "Every column the business treats as sensitive (SSN, tax id and the like), per "
           "table: raw or hashed, whether its dataset is restricted, and exposure findings.", {}, []),
    schema("search_tables", "Find tables by meaning. Ranks by what the tables hold and how much the business uses "
           "them. Each result carries its status (current / caution / avoid), why, and what to use instead.",
           {"query": S}, ["query"]),
    schema("find_tables_by_name", "Find tables by name: a glob (CC*, *_hist) or a substring. Use for questions "
           "about table names.", {"pattern": S}, ["pattern"]),
    schema("describe_table", "Everything the usage evidence says about one table: what it holds, whether to use "
           "it and why, its columns with the variable each one is, how the business filters and joins it, "
           "where its data comes from, who uses it, findings, and sample SQL that uses it.", {"table": S}, ["table"]),
    schema("join_path", "How to join a set of tables: the join columns the business actually uses (production "
           "models first), through intermediate tables if needed, plus joins known to be wrong.",
           {"tables": {"type": "array", "items": S}}, ["tables"]),
    schema("find_columns", "Find columns by meaning or name, grouped by the variable (the real-world thing) they "
           "hold, with each table's status. Sensitive columns are marked raw or hashed.", {"query": S}, ["query"]),
    schema("column_detail", "One column: its variable, where its values come from (lineage and the functions "
           "applied), the literal values queries filter it on and when, and findings.",
           {"column": {"type": "string", "description": "dataset.table.column or project.dataset.table.column"}}, ["column"]),
    schema("dry_run", "Validate BigQuery SQL with a dry run (free, reads no data). Use the table names as given "
           "by the other tools. Also reports the status of every table the SQL reads.", {"sql": S}, ["sql"]),
]
CATALOG_TOOLS = [
    schema("list_tables", "List tables whose name (table, dataset.table or project.dataset.table) matches a glob or "
           "substring ('*' for all).", {"pattern": S}, ["pattern"]),
    schema("table_schema", "Columns and types of one table, and its partitioning and clustering.", {"table": S}, ["table"]),
    schema("search_columns", "Find columns by name: a glob or substring, across all tables.", {"pattern": S}, ["pattern"]),
    schema("dry_run", "Validate BigQuery SQL with a dry run (free, reads no data).", {"sql": S}, ["sql"]),
]
