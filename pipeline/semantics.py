#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "neo4j>=5.20", "anthropic>=0.40"]
# ///
"""Stage 6: name and describe what the graph already has, and embed it.

The LLM only names structure that usage already established - tables, variables,
subjects - from the evidence the graph holds about each: columns and their variables,
lineage, which tables are queried together, who consumes it, a sample query, findings.
It never adds structure, with one labelled exception: it *proposes* domains (groups of
subjects), stored as proposed, for a person to confirm.

Abbreviations come from the business's own renames first: when lineage renames BRNCH_ID
to branch_id or FEE_TYP_CD to fee_type_code, the tokens line up. That glossary is given
to the model, which expands each abbreviation per object from context ("CC" means credit
card, contact center or cost center depending on the table).

Output contract (forced through a tool schema) and validation before anything is stored:
names of 1-6 words, descriptions of 20-400 characters that add to the name, no assistant
boilerplate, and no identifiers that are not in the evidence. A failure is retried once
with the error; a second failure is recorded (description_status = failed), never dropped.

Embeddings: one structured document per table, subject and variable, embedded with
Azure OpenAI text-embedding-3-large at 512 dimensions, mean-centered per label and
normalized, stored on the node with a cosine vector index. The per-label mean is kept
on (:EmbeddingSpace) so queries are centered the same way (pipeline/retrieve.py).

Caches: work/llm_cache/, work/emb_cache.json (keyed by input hash).

Usage: uv run pipeline/semantics.py [--only tables|variables|subjects|domains|embed]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anthropic

from graphdb import Graph, config, env
from llm import Embedder, prompt  # Embedder re-exported for retrieve.py / tools.py

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
CACHE = WORK / "llm_cache"
BOILERPLATE = re.compile(r"(?i)\b(okay|sure|certainly|as an ai|i understand|please provide|i can|i will|"
                         r"here (is|are)|let me|i'm unable|i cannot)\b")
SYSTEM = prompt("describe_system")


# ------------------------------------------------------------------ glossary

def mine_glossary(G: Graph) -> dict[str, Counter]:
    """Abbreviation -> expansions, from renames in lineage (BRNCH_ID -> branch_id)."""
    gl = defaultdict(Counter)
    for r in G.rows("""MATCH (a:Column)-[f:FLOWS]->(b:Column) WHERE 'rename' IN f.kinds
                       RETURN a.name AS a, b.name AS b"""):
        ta = [t for t in re.split(r"[_\W]+|(?<=[a-z])(?=[A-Z])", r["a"]) if t]
        tb = [t for t in re.split(r"[_\W]+", r["b"].lower()) if t]
        if len(ta) < len(tb):       # initialisms: CC_ID -> cost_center_id gives CC = cost center
            i = j = 0
            while i < len(ta) and j < len(tb):
                x = ta[i].upper()
                if 2 <= len(x) <= 4 and x.isalpha() and j + len(x) <= len(tb) and \
                        "".join(w[0] for w in tb[j:j + len(x)]).upper() == x and x.lower() != tb[j]:
                    gl[x][" ".join(tb[j:j + len(x)])] += 1
                    i, j = i + 1, j + len(x)
                elif x.lower() == tb[j]:
                    i, j = i + 1, j + 1
                else:
                    break
            continue
        if len(ta) != len(tb):
            continue
        for x, y in zip(ta, tb):
            x = x.upper()
            if x.lower() != y and len(x) <= 6 and x[0].lower() == y[0] and len(y) > len(x):
                gl[x][y] += 1
    return {k: v for k, v in gl.items() if sum(v.values()) >= 1}


# ---------------------------------------------------------------------- LLM

class LLM:
    def __init__(self, cfg):
        self.model = cfg["llm"]["model"]
        self.client = anthropic.Anthropic(api_key=env()["ANTHROPIC_API_KEY"])
        CACHE.mkdir(parents=True, exist_ok=True)
        self.calls = self.cached = 0
        self.tokens = Counter()

    def call(self, user: str, schema: dict, tool: str) -> dict:
        key = hashlib.sha256(json.dumps([self.model, SYSTEM, user, schema]).encode()).hexdigest()
        path = CACHE / f"{key}.json"
        if path.exists():
            self.cached += 1
            return json.loads(path.read_text())
        for attempt in range(4):
            try:
                resp = self.client.messages.create(
                    model=self.model, max_tokens=8000, system=SYSTEM,
                    tools=[{"name": tool, "description": "Record the results.", "input_schema": schema}],
                    tool_choice={"type": "tool", "name": tool},
                    messages=[{"role": "user", "content": user}])
                break
            except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError):
                time.sleep(2 ** attempt * 3)
        else:
            raise RuntimeError("LLM unavailable")
        self.calls += 1
        self.tokens["in"] += resp.usage.input_tokens
        self.tokens["out"] += resp.usage.output_tokens
        out = next(b.input for b in resp.content if b.type == "tool_use")
        path.write_text(json.dumps(out))
        return out


ITEM_SCHEMA = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string", "description": "2-5 words"},
            "description": {"type": "string", "description": "1-2 sentences"},
            "confidence": {"type": "number", "description": "0-1: how clearly the evidence shows this"},
            "abbreviations": {"type": "array", "items": {
                "type": "object", "properties": {"abbr": {"type": "string"}, "expansion": {"type": "string"}},
                "required": ["abbr", "expansion"]}},
        },
        "required": ["id", "name", "description", "confidence", "abbreviations"]}}},
    "required": ["items"]}


def validate(item: dict, known_ids: set[str], name_words=(1, 6), own_tokens: set[str] = frozenset()) -> str | None:
    n, d = (item.get("name") or "").strip(), (item.get("description") or "").strip()
    if not n or not name_words[0] <= len(n.split()) <= name_words[1]:
        return f"name must be {name_words[0]}-{name_words[1]} words"
    if not 20 <= len(d) <= 400:
        return "description must be 20-400 characters"
    if BOILERPLATE.search(n) or BOILERPLATE.search(d[:60]):
        return "no assistant boilerplate - describe the object"
    extra = {w for w in re.findall(r"[a-z]+", d.lower()) if len(w) > 3} - {w for w in re.findall(r"[a-z]+", n.lower())}
    if len(extra) < 4:
        return "the description must say more than the name"
    for ref in re.findall(r"`([^`]+)`", d):
        if ref.lower() not in known_ids:
            return f"'{ref}' is not in the evidence"
    # the name and the abbreviation list must agree ("Contact Center ..." with CC = cost center does not),
    # for the abbreviations in the object's own name
    words = [w.strip("(),.") for w in n.split()]
    for ab in item.get("abbreviations") or []:
        a, e = (ab.get("abbr") or "").upper(), (ab.get("expansion") or "").lower()
        if not 2 <= len(a) <= 4 or not a.isalpha() or a not in own_tokens:
            continue
        spans = [" ".join(words[i:i + len(a)]) for i in range(len(words) - len(a) + 1)
                 if "".join(w[0] for w in words[i:i + len(a)] if w).upper() == a]
        stem = lambda x: " ".join(w.rstrip("s") for w in x.lower().split())
        if spans and stem(e) not in (stem(x) for x in spans):
            return f"the name spells {a} as '{spans[0]}' but the abbreviations say '{ab.get('expansion')}'"
    return None


def describe(llm: LLM, contexts: list[dict], batch: int, kind: str, pool) -> dict[str, dict]:
    """Run batches, validate, retry failures once one by one. -> id -> result."""
    def known(ctx):
        return {x.lower() for x in ctx.get("_refs", [])}

    def run(ctxs):
        body = prompt("describe_batch", n=len(ctxs), kind=kind, evidence="\n\n".join(c["text"] for c in ctxs))
        out = llm.call(body, ITEM_SCHEMA, f"record_{kind}")
        return {i.get("id"): i for i in out.get("items", [])}

    batches = [contexts[i:i + batch] for i in range(0, len(contexts), batch)]
    results = {}
    for got in pool.map(run, batches):
        results.update(got)
    final, retry = {}, []
    for c in contexts:
        item = results.get(c["id"])
        err = "missing from the answer" if item is None else validate(item, known(c), own_tokens=c.get("_tokens", set()))
        (retry.append((c, err)) if err else final.__setitem__(c["id"], {**item, "status": "ok"}))

    def redo(pair):
        c, err = pair
        body = prompt("describe_retry", kind=kind[:-1] if kind.endswith("s") else kind, error=err, evidence=c["text"])
        out = llm.call(body, ITEM_SCHEMA, f"record_{kind}")
        item = next((i for i in out.get("items", []) if i.get("id") == c["id"]), (out.get("items") or [None])[0])
        e2 = "missing" if not item else validate(item, known(c), own_tokens=c.get("_tokens", set()))
        return c["id"], ({**item, "id": c["id"], "status": "retried"} if not e2 else
                         {"id": c["id"], "status": "failed", "error": e2, "name": None, "description": None,
                          "confidence": 0, "abbreviations": []})
    for cid, item in pool.map(redo, retry):
        final[cid] = item
    return final


# ------------------------------------------------------------------ contexts

def gloss_for(names: list[str], glossary) -> str:
    toks = {t.upper() for n in names for t in re.split(r"[_\W]+", n) if t}
    hits = [f"{t} = {', '.join(w for w, _ in glossary[t].most_common(3))}" for t in sorted(toks) if t in glossary]
    return ("How other tables rename these abbreviations (may not apply here - decide from this object's own "
            "evidence): " + "; ".join(hits)) if hits else ""


def table_contexts(G: Graph, glossary) -> list[dict]:
    T = {r["t"]["id"]: r["t"] for r in G.rows("""MATCH (t:Table) WHERE t.in_catalog
        OPTIONAL MATCH (t)-[:IN_SUBJECT]->(s:Subject)
        RETURN t {.id, .name, .kind, .layer, .consumed_jobs, .consumer_count, .written_jobs, .last_written,
                  subject: s.id} AS t""")}
    cols = defaultdict(list)
    for r in G.rows("""MATCH (t:Table)-[:HAS_COLUMN]->(c:Column) OPTIONAL MATCH (c)-[:IS]->(v:Variable)
                       RETURN t.id AS t, c.name AS c, c.type AS type, v.name AS v, v.role AS role, v.hub AS hub,
                              v.size AS vsize"""):
        cols[r["t"]].append(r)
    # a column usage never connects is placed by its name, as M3 does: the one well-used
    # identifier that has a column of the same name elsewhere
    same_name = defaultdict(set)
    for r in G.rows("""MATCH (v:Variable {role: 'identifier'})<-[:IS]-(c:Column) WHERE v.joined_tables >= 2
                       RETURN toLower(c.name) AS n, v.name AS v"""):
        same_name[r["n"]].add(r["v"])
    src = defaultdict(set)
    for r in G.rows("MATCH (a:Table)-[:DERIVED_FROM]->(b:Table) RETURN a.id AS a, b.id AS b"):
        src[r["a"]].add(r["b"])
    co = defaultdict(Counter)
    for r in G.rows("""MATCH (s:QueryShape {succeeded: true})-[:REFERENCES]->(a:Table), (s)-[:REFERENCES]->(b:Table)
                       WHERE a <> b AND s.purpose IN ['adhoc', 'bi', 'extract', 'build'] AND b.in_catalog
                       RETURN a.id AS a, b.id AS b, sum(s.jobs) AS n"""):
        co[r["a"]][r["b"]] += r["n"]
    who = defaultdict(Counter)
    for r in G.rows("""MATCH (p:Principal)-[c:CONSUMES]->(t:Table) OPTIONAL MATCH (p)-[:MEMBER_OF]->(tm:Team)
                       RETURN t.id AS t, p.class AS cls, tm.top_datasets AS team, split(p.id, '@')[0] AS p, c.jobs AS n"""):
        who[r["t"]][r["cls"] if r["cls"] != "human" else f"analyst {r['p']}"] += r["n"]
    sample = {}
    for r in G.rows("""MATCH (s:QueryShape {succeeded: true})-[:REFERENCES]->(t:Table)
                       WHERE s.purpose IN ['adhoc', 'bi', 'build', 'view_definition']
                       WITH t, s ORDER BY s.jobs DESC WITH t, collect(s.sample_sql)[0] AS q RETURN t.id AS t, q"""):
        sample[r["t"]] = r["q"]
    fnd = defaultdict(list)
    for r in G.rows("""MATCH (f:Finding)-[a:ABOUT]->(t:Table) WHERE a.role IN ['subject', 'built_by_it', 'exposed', 'copy', 'original']
                       RETURN t.id AS t, f.title AS title"""):
        fnd[r["t"]].append(r["title"])
    # findings about its columns carry evidence too: a suspect join names the id spaces involved
    for r in G.rows("""MATCH (f:Finding)-[:ABOUT]->(c:Column)<-[:HAS_COLUMN]-(t:Table)
                       WHERE f.kind IN ['suspect_join', 'unit_mismatch', 'pii_exposure', 'pii_candidate', 'literal_drift']
                       RETURN t.id AS t, f.title + ': ' + left(f.summary, 220) AS title"""):
        fnd[r["t"]].append(r["title"])
    out = []
    for t, m in T.items():
        cs = cols[t][:45]
        for c in cs:
            c["alias"] = None
            if (c["vsize"] or 1) <= 3 and len(same_name.get(c["c"].lower(), ())) == 1:
                other = next(iter(same_name[c["c"].lower()]))
                if other.lower() != (c["v"] or "").lower():
                    c["alias"] = other
        lines = [f"### table {t}",
                 f"id: {t}", f"kind: {m['kind']}, layer (from who writes it): {m.get('layer')}"
                 f", written {m.get('written_jobs') or 0} times in the window, consumed by {m.get('consumer_count') or 0} "
                 f"principals ({m.get('consumed_jobs') or 0} jobs)",
                 "columns: " + "; ".join(
                     f"{c['c']} {c['type'] or ''}" + (f" [probably the same id as '{c['alias']}' elsewhere (same column name)]" if c["alias"] else "")
                     + (f" [same thing as '{c['v']}', used as {c['role']}{', a key used estate-wide' if c['hub'] else ''}]"
                                                    if c["v"] and c["v"].lower() != c["c"].lower() else
                                                    (f" [used as {c['role']}]" if c["role"] else ""))
                     for c in cs) + (" ..." if len(cols[t]) > 45 else "")]
        if src[t]:
            lines.append("built from: " + ", ".join(sorted(src[t])[:8]))
        if co[t]:
            lines.append("queried together with: " + ", ".join(x for x, _ in co[t].most_common(6)))
        if who[t]:
            lines.append("used by: " + ", ".join(f"{k}" for k, _ in who[t].most_common(5)))
        g = gloss_for([m["name"]] + [c["c"] for c in cs], glossary)
        if g:
            lines.append(g)
        if fnd[t]:
            lines.append("findings about it: " + "; ".join(fnd[t][:4]))
        if sample.get(t):
            lines.append("sample SQL that uses it:\n" + sample[t][:700])
        out.append({"id": t, "text": "\n".join(lines),
                    "_tokens": {x.upper() for x in re.split(r"[_\W]+", m["name"]) if x},
                    "_refs": [t, m["name"]] + [c["c"] for c in cols[t]] + list(src[t]) + [x for x in co[t]]})
    return out


def variable_contexts(G: Graph, glossary, tdesc: dict) -> list[dict]:
    V = G.rows("""MATCH (v:Variable)<-[:IS]-(c:Column)<-[:HAS_COLUMN]-(t:Table)
                  WITH v, collect(DISTINCT {c: c.name, t: t.id, type: c.type}) AS ms
                  OPTIONAL MATCH (v)-[:IDENTIFIES]->(e:Entity)
                  RETURN v {.id, .name, .role, .hub, .tables, .datasets, .names} AS v, ms, e.name AS entity""")
    vals = defaultdict(list)
    for r in G.rows("""MATCH (v:Variable)<-[:IS]-(c:Column)-[h:HAS_VALUE]->(l:Literal)
                       WITH v, l.value AS val, sum(h.jobs) AS n ORDER BY n DESC
                       RETURN v.id AS v, collect(val)[0..8] AS vals"""):
        vals[r["v"]] = r["vals"]
    out = []
    for r in V:
        v, ms = r["v"], r["ms"]
        ms = sorted(ms, key=lambda x: (tdesc.get(x["t"], {}).get("status") != "ok", x["t"]))[:14]
        lines = [f"### variable {v['id']}", f"id: {v['id']}",
                 f"used as: {v['role']}" + (" - a key most of the warehouse uses" if v["hub"] else "")
                 + (f"; one of the ids of the entity '{r['entity']}'" if r["entity"] else ""),
                 f"appears as {v['tables']} columns in {v['datasets']} datasets, spelled: {', '.join(v['names'][:12])}",
                 "columns (table - what the table is): " + "; ".join(
                     f"{m['t'].split('.', 1)[1]}.{m['c']} {m['type'] or ''}"
                     + (f" - {tdesc[m['t']]['name']}" if tdesc.get(m["t"], {}).get("name") else "") for m in ms)]
        if vals.get(v["id"]):
            lines.append("values seen in filters: " + ", ".join(repr(x) for x in vals[v["id"]]))
        g = gloss_for(v["names"], glossary)
        if g:
            lines.append(g)
        out.append({"id": v["id"], "text": "\n".join(lines), "_refs": [v["id"]] + v["names"] + [m["c"] for m in r["ms"]]})
    return out


def subject_contexts(G: Graph, tdesc: dict) -> list[dict]:
    S = G.rows("""MATCH (s:Subject)<-[:IN_SUBJECT]-(t:Table)
                  WITH s, collect(t.id) AS ts
                  OPTIONAL MATCH (s)-[k:KEYED_BY]->(v:Variable)
                  WITH s, ts, collect(DISTINCT v.name) AS hubs
                  OPTIONAL MATCH (s)-[l:LINKED]-(o:Subject)
                  RETURN s {.id, .name, .kind} AS s, ts, hubs, collect(DISTINCT o.id)[0..6] AS linked""")
    out = []
    for r in S:
        s = r["s"]
        lines = [f"### subject {s['id']}", f"id: {s['id']}",
                 f"a group of tables that share their own keys and columns ({s['kind']})"
                 + (f"; keyed by the estate-wide keys {', '.join(r['hubs'][:5])}" if r["hubs"] else ""),
                 "tables: " + "; ".join(f"{t.split('.', 1)[1]}" + (f" - {tdesc[t]['name']}: {tdesc[t]['description']}"
                                                                   if tdesc.get(t, {}).get("description") else "")
                                        for t in sorted(r["ts"])[:16])]
        out.append({"id": s["id"], "text": "\n".join(lines), "_refs": [s["id"]] + r["ts"] + [t.split(".")[-1] for t in r["ts"]]})
    return out


SENSE_SCHEMA = {"type": "object", "properties": {
    "abbr": {"type": "string"}, "expansion": {"type": "string"},
    "evidence": {"type": "string", "description": "the facts in the evidence that decide it"}},
    "required": ["abbr", "expansion", "evidence"]}


def disambiguate(llm: LLM, contexts: list[dict], results: dict, pool) -> dict[str, dict]:
    """Abbreviations in object names that the estate expands more than one way (CC: credit card,
    contact center, cost center) get a focused question per object; the answer is then a fact
    in that object's evidence and it is described again."""
    senses = defaultdict(set)
    for cid, r in results.items():
        for ab in r.get("abbreviations") or []:
            a = (ab.get("abbr") or "").upper()
            if a in next((c["_tokens"] for c in contexts if c["id"] == cid), set()):
                senses[a].add((ab.get("expansion") or "").strip().lower())
    ambiguous = {a: sorted(e for e in es if e) for a, es in senses.items() if len({e for e in es if e}) >= 2}
    todo = [(c, a) for c in contexts for a in ambiguous if a in c.get("_tokens", set())]

    def ask(pair):
        c, a = pair
        body = prompt("abbreviation_sense", abbr=a, senses=", ".join(ambiguous[a]), object=c["id"], evidence=c["text"])
        return c["id"], a, llm.call(body, SENSE_SCHEMA, "record_sense")
    fixed = defaultdict(dict)
    for cid, a, out in pool.map(ask, todo):
        fixed[cid][a] = out
    return {"ambiguous": ambiguous, "fixed": dict(fixed)}


DOMAIN_SCHEMA = {"type": "object", "properties": {"domains": {"type": "array", "items": {
    "type": "object", "properties": {"name": {"type": "string"}, "description": {"type": "string"},
                                     "subjects": {"type": "array", "items": {"type": "string"}}},
    "required": ["name", "description", "subjects"]}}}, "required": ["domains"]}


# ---------------------------------------------------------------- embeddings

def center(vecs: list[list[float]]) -> tuple[list[list[float]], list[float]]:
    n, d = len(vecs), len(vecs[0])
    mean = [sum(v[i] for v in vecs) / n for i in range(d)]
    out = []
    for v in vecs:
        c = [x - m for x, m in zip(v, mean)]
        norm = math.sqrt(sum(x * x for x in c)) or 1.0
        out.append([x / norm for x in c])
    return out, mean


# --------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["tables", "variables", "subjects", "domains", "embed"])
    a = ap.parse_args()
    cfg = config()
    G = Graph()
    llm = LLM(cfg)
    pool = ThreadPoolExecutor(cfg["llm"].get("concurrency", 6))
    glossary = mine_glossary(G)
    t0 = time.time()
    stats = {}

    def store(label, results):
        G.batch(f"{label}.describe", f"""UNWIND $rows AS r MATCH (n:{label} {{id: r.id}})
            SET n.display_name = r.name, n.description = r.description, n.description_status = r.status,
                n.description_error = r.error,
                n.description_confidence = r.confidence, n.abbreviations = r.abbr, n.described_by = r.model""",
                [{"id": k, "name": v.get("name"), "description": v.get("description"), "status": v["status"],
                  "confidence": v.get("confidence"), "abbr": json.dumps(v.get("abbreviations") or []),
                  "model": llm.model, "error": v.get("error")} for k, v in results.items()])
        stats[label] = Counter(v["status"] for v in results.values())

    def load(label):
        return {r["id"]: {"name": r["n"], "description": r["d"], "status": r["s"]} for r in G.rows(
            f"MATCH (n:{label}) RETURN n.id AS id, n.display_name AS n, n.description AS d, n.description_status AS s")}

    if a.only in (None, "tables"):
        tctx = table_contexts(G, glossary)
        tres = describe(llm, tctx, 8, "tables", pool)
        amb = disambiguate(llm, tctx, tres, pool)
        if amb["fixed"]:
            redo = []
            for c in tctx:
                if c["id"] in amb["fixed"]:
                    facts = "; ".join(f"{a} in this table's name means {v['expansion']} ({v['evidence'][:160]})"
                                      for a, v in amb["fixed"][c["id"]].items())
                    redo.append({**c, "text": c["text"] + f"\nSettled: {facts}."})
            tres.update(describe(llm, redo, 4, "tables", pool))
        stats["ambiguous abbreviations"] = {a: len(v) for a, v in amb["ambiguous"].items()}
        store("Table", tres)
    tdesc = load("Table")
    if a.only in (None, "variables"):
        store("Variable", describe(llm, variable_contexts(G, glossary, tdesc), 20, "variables", pool))
    if a.only in (None, "subjects"):
        store("Subject", describe(llm, subject_contexts(G, tdesc), 8, "subjects", pool))
    if a.only in (None, "domains"):
        sdesc = load("Subject")
        lines = [f"- {sid}: {d['name'] or sid} - {d['description'] or ''}" for sid, d in sorted(sdesc.items())]
        out = llm.call(prompt("domains", subjects="\n".join(lines)), DOMAIN_SCHEMA, "record_domains")
        assigned = {}
        for d in out.get("domains", []):
            for sid in d["subjects"]:
                if sid in sdesc and sid not in assigned:
                    assigned[sid] = d["name"]
        missing = [s for s in sdesc if s not in assigned]
        G.auto("MATCH (d:Domain) CALL (d) { DETACH DELETE d } IN TRANSACTIONS OF 1000 ROWS")
        G.batch("Domain", """UNWIND $rows AS r MERGE (d:Domain {id: r.name}) SET d.description = r.desc,
            d.status = 'proposed', d.proposed_by = r.model""",
                [{"name": d["name"], "desc": d["description"], "model": llm.model} for d in out.get("domains", [])])
        G.batch("CONTAINS", """UNWIND $rows AS r MATCH (d:Domain {id: r.d}), (s:Subject {id: r.s}) MERGE (d)-[:CONTAINS]->(s)""",
                [{"d": v, "s": k} for k, v in assigned.items()])
        stats["Domain"] = {"domains": len(out.get("domains", [])), "unassigned": len(missing)}
    if a.only in (None, "embed"):
        emb = Embedder(cfg)
        docs = {
            "Table": G.rows("""MATCH (t:Table) WHERE t.in_catalog AND t.description IS NOT NULL
                OPTIONAL MATCH (t)-[:IN_SUBJECT]->(s:Subject)
                OPTIONAL MATCH (t)-[:HAS_COLUMN]->(c:Column)
                WITH t, s, collect(c.name)[0..40] AS cols
                RETURN t.id AS id, t.display_name + '. ' + t.description + ' Table ' + t.id + '. Subject: ' +
                       coalesce(s.display_name, '') + '. Columns: ' + reduce(x = '', c IN cols | x + c + ' ') AS doc"""),
            "Subject": G.rows("""MATCH (s:Subject)<-[:IN_SUBJECT]-(t:Table) WHERE s.description IS NOT NULL
                WITH s, collect(coalesce(t.display_name, t.name))[0..20] AS ts
                RETURN s.id AS id, s.display_name + '. ' + s.description + ' Tables: ' + reduce(x = '', n IN ts | x + n + '; ') AS doc"""),
            "Variable": G.rows("""MATCH (v:Variable) WHERE v.description IS NOT NULL
                RETURN v.id AS id, v.display_name + '. ' + v.description + ' Columns: ' +
                       reduce(x = '', n IN v.names | x + n + ' ') AS doc"""),
        }
        for label, rows in docs.items():
            vecs, mean = center(emb.embed([r["doc"] for r in rows]))
            G.batch(f"{label}.embedding", f"""UNWIND $rows AS r MATCH (n:{label} {{id: r.id}}) SET n.embedding = r.e""",
                    [{"id": r["id"], "e": v} for r, v in zip(rows, vecs)], size=500)
            G.run("MERGE (e:EmbeddingSpace {id: $l}) SET e.mean = $m, e.dims = $d, e.model = $model, e.centered = true",
                  l=label, m=mean, d=len(mean), model=cfg["embeddings"]["deployment"])
            G.run(f"""CREATE VECTOR INDEX {label.lower()}_embedding IF NOT EXISTS FOR (n:{label}) ON n.embedding
                     OPTIONS {{indexConfig: {{`vector.dimensions`: {len(mean)}, `vector.similarity_function`: 'cosine'}}}}""")
            stats[f"{label}.embedded"] = len(rows)
    pool.shutdown()
    cost = llm.tokens["in"] / 1e6 * 1.0 + llm.tokens["out"] / 1e6 * 5.0
    print(f"{time.time() - t0:.0f}s; LLM {llm.model}: {llm.calls} calls, {llm.cached} cached, "
          f"{llm.tokens['in']:,} in / {llm.tokens['out']:,} out tokens (~${cost:.2f}); glossary {len(glossary)} abbreviations")
    for k, v in stats.items():
        print(f"  {k}: {dict(v) if isinstance(v, Counter) else v}")
    G.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
