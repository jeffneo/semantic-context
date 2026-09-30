"""Distill: skills from the agents' own experience (plans/2026-09-29-context-memory-model.md; memory phase 4).

The method qlsc applies to the warehouse's query log, applied to the agents' record in memory:
  path       a task's steps' fingerprints, in order (qlsc/converse.py: a recall is 'recall <Label> ?', an ask
             its compiled request with every value out). Only tasks of distill.min_steps steps or more:
             one tool call is using a tool, not a procedure
  success    a task that closed, every step of which ran, and that no rating or outcome called a failure
             (distill.negative)
  cluster    tasks as nodes, joined where the steps and tables they share (Jaccard) reach distill.similarity;
             Leiden, seeded and single-threaded, as qlsc's builds are
  distill    from each cluster of distill.min_support tasks or more, with a success rate of at least
             distill.min_success: a Skill. Its procedure is the cluster's most common successful path, written
             from the fingerprints (schema only, no text); the LLM names it from the procedure and the
             cluster's requests with every literal masked (prompts/skill_*.md). A skill is its procedure:
             distilling again updates its support; a different best path for the same tasks supersedes it
             (because: improved)
  approve    a person approves a proposed skill (`qlsc skills --approve`), recorded as a Fact about it: only an
             approved skill is offered, and fed back
  offer      at a new task, the approved skills whose trigger is closest to its request (embeddings, the
             request masked), at most distill.offers, and only those whose every table the reader may read
  measure    a task whose path matches an approved skill's (Jaccard, distill.similarity) -[:FOLLOWED]-> it.
             Its uses and successes count them; one whose followers succeed less than distill.retire_below,
             over distill.min_support uses, is retired
  security   a skill is shared, and holds no values: its procedure is fingerprints; its name, description and
             trigger come from masked requests and are checked against every literal of its evidence. Its
             evidence (the tasks it came FROM) stays private: others see how many, not which. It is ABOUT the
             stubs of the tables its steps read, and shown only to readers who may read them all
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import uuid
from collections import Counter

from qlsc import memory
from qlsc.config import Settings
from qlsc.llm import LLM, Embedder, cosine, prompt

DISTILLER = "distilled"  # a skill's owner: the memory service, not a principal
_EMBEDDERS: dict[str, Embedder] = {}  # one per work directory: its cache file is large

EXPERIENCE = """
MATCH (t:Task) WHERE t.status IN ['done', 'failed'] AND ($id IS NULL OR t.id = $id)
MATCH (s:Step)-[:PART_OF]->(t)
WITH t, s ORDER BY s.seq
WITH t, collect(s {.fingerprint, .status, .arguments, .result}) AS steps
RETURN t.id AS id, t.owner AS owner, t.request AS request, t.status AS status, steps,
       [(f:Fact {predicate: 'rated'})-[:ABOUT]->(t) | f.value]
       + [(t)<-[:PART_OF]-(:Decision)<-[:ABOUT]-(o:Fact {predicate: 'outcome'}) | o.value] AS verdicts,
       [(t)<-[:PART_OF]-(:Step)-[:READ]->(x:Table) | x.id]
       + [(t)<-[:PART_OF]-(:Step)-[:READ {context: true}]->(n) | labels(n)[0]] AS reads
ORDER BY id
"""
SKILLS = """
MATCH (k:Skill)
RETURN k.id AS id, k.key AS key, k.name AS name, k.status AS status, k.fingerprints AS fingerprints,
       k.tables AS tables, k.embedding AS embedding, k.trigger AS trigger, k.description AS description,
       k.procedure AS procedure, k.support AS support, k.success_rate AS success_rate, k.uses AS uses,
       k.successes AS successes, k.version AS version, [(k)-[:FROM]->(t:Task) | t.id] AS evidence
ORDER BY k.name
"""
SKILL = """
MERGE (k:Skill {key: $key})
ON CREATE SET k.id = $id, k.status = 'proposed', k.version = $version, k.recorded_at = $now, k.owner = $owner,
              k.scope = 'shared', k.uses = 0, k.successes = 0, k.name = $name, k.description = $description,
              k.trigger = $trigger, k.embedding = $embedding
SET k.fingerprints = $fingerprints, k.procedure = $procedure, k.parameters = $parameters, k.tables = $tables,
    k.support = $support, k.success_rate = $rate, k.distilled_at = $now
WITH k
UNWIND $evidence AS e
MATCH (t:Task {id: e})
MERGE (k)-[:FROM]->(t)
WITH DISTINCT k
UNWIND $tables AS tb
MERGE (x:Table {id: tb})
MERGE (k)-[:ABOUT]->(x)
"""
SUPERSEDE = """
MATCH (new:Skill {key: $new}), (old:Skill {key: $old}) WHERE NOT (new)-[:SUPERSEDES]->(old)
SET old.status = 'retired', new.version = coalesce(old.version, 1) + 1
CREATE (new)-[:SUPERSEDES {because: 'improved'}]->(old)
"""
FOLLOWERS = """
MATCH (k:Skill {id: $id})<-[:FOLLOWED]-(t:Task)
RETURN t.id AS id
"""
STATS = "MATCH (k:Skill {id: $id}) SET k.uses = $uses, k.successes = $successes"
RETIRE = """
MATCH (k:Skill {id: $id}) WHERE k.status = 'approved'
SET k.status = 'retired'
CREATE (f:Fact {id: $fact, predicate: 'retired', value: $why, origin: 'distilled', valid_from: $now,
                recorded_at: $now, owner: $owner, scope: 'shared'})-[:ABOUT]->(k)
"""
APPROVE = """
MATCH (k:Skill {id: $id}) WHERE k.status = 'proposed'
SET k.status = 'approved', k.approved_by = $by, k.approved_at = $now
CREATE (f:Fact {id: $fact, predicate: 'approved', value: $by, origin: 'user', valid_from: $now, recorded_at: $now,
                owner: $by, scope: 'shared'})-[:ABOUT]->(k)
RETURN k.name AS name
"""
FOLLOW = """
MATCH (t:Task {id: $task}), (k:Skill {id: $skill})
MERGE (t)-[:FOLLOWED]->(k)
"""
COMPUTATION_NAMES = "MATCH (c:Computation) WHERE c.name IS NOT NULL RETURN c.id AS id, c.name AS name"
NAME_SCHEMA = {
    "type": "object",
    "required": ["name", "description", "trigger"],
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "trigger": {"type": "string"},
    },
}
MASKS = [
    (re.compile(r"'[^']*'|\"[^\"]*\""), "{value}"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "{date}"),
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "{value}"),
    (re.compile(r"\S+@\S+\.\w+"), "{value}"),
    (re.compile(r"-?\b\d{3,}\b"), "{value}"),
]


def embedder(s: Settings) -> Embedder:
    if str(s.work) not in _EMBEDDERS:
        _EMBEDDERS[str(s.work)] = Embedder(s)
    return _EMBEDDERS[str(s.work)]


def mask(text: str) -> str:
    """A request with its literals out: quoted strings, dates, ids, emails, and numbers of three digits or
    more ('last 90 days' keeps its 90)."""
    for pattern, placeholder in MASKS:
        text = pattern.sub(placeholder, text)
    return text


def literals(task: dict) -> set[str]:
    """What a task named: every masked-out literal of its request, its steps' arguments and their queries."""
    texts = [task["request"] or ""]
    for s in task["steps"]:
        texts += [
            s.get("arguments") or "",
            json.dumps((json.loads(s.get("result") or "{}") or {}).get("query", "")),
        ]
    found = set()
    for text in texts:
        for pattern, _ in MASKS:
            found |= {m.strip("'\"") for m in pattern.findall(text) if len(m.strip("'\"")) >= 3}
    return found


def experience(M, label_table: dict[str, str], task: str | None = None) -> list[dict]:
    """The closed tasks with steps (or one), each with what it read as layer tables: a recall's anchor label
    as its table."""
    rows = M.rows(EXPERIENCE, id=task)
    return [t | {"reads": sorted({label_table.get(r, r) for r in t["reads"]})} for t in rows]


def skill_features(k: dict) -> set[str]:
    return set(k["fingerprints"] or []) | set(k["tables"] or [])


def success(task: dict, negative: list[str]) -> bool:
    return (
        task["status"] == "done"
        and all(s["status"] == "ok" for s in task["steps"])
        and not any(v in negative for v in task["verdicts"])
    )


def path(task: dict) -> tuple[str, ...]:
    return tuple(s["fingerprint"] or "" for s in task["steps"])


def features(task: dict) -> set[str]:
    """What a task did and read, for similarity: its step fingerprints and the tables and labels it read."""
    return set(path(task)) | set(task["reads"])


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def readable_step(fp: str, computations: dict[str, str] | None = None) -> str:
    """A fingerprint, written for a person, from the schema alone (a Computation by its name): no request
    text."""
    named = lambda c: (computations or {}).get(c, f"Computation {c}")
    if fp.startswith("recall "):
        return f"recall the {fp.split()[1]}'s context"
    if fp.startswith("ask {"):
        shape = json.loads(fp[4:])
        cols = lambda xs, k="column": [x.get(k) or x.get("computation", "") for x in xs]
        short = lambda c: ".".join(str(c).split(".")[-2:])
        measures = [f"{m.get('aggregate') or 'COUNT'}({short(m.get('column', 'rows'))})" if m.get("aggregate") or m.get("column") else named(m.get("computation")) for m in shape.get("measures", [])]  # fmt: skip
        by = [short(c) for c in cols(shape.get("dimensions", []))]
        where = [
            f"{short(f.get('column') or f.get('computation'))} {f.get('op', '=')} ?"
            for f in shape.get("filters", [])
        ]
        period = shape.get("period", {}).get("column")
        text = "ask " + ", ".join(measures)
        text += f" by {', '.join(by)}" if by else ""
        text += f" where {' and '.join(where)}" if where else ""
        text += f" over a period of {short(period)}" if period else ""
        return text
    return fp


def model_tables(m: memory.Model) -> dict[str, str]:
    """A virtual graph label -> its layer table."""
    return {label: t["id"] for label, t in m.tables.items()}


def distill(s: Settings, now: dt.datetime | None = None) -> list[dict]:
    """Every skill the agents' experience supports, proposed (or updated), and the approved ones measured.
    -> the skills, as memory holds them after."""
    now, p = now or dt.datetime.now(dt.UTC), s["distill"]
    ds = memory.reader_model(s, None)
    label_table = model_tables(ds)
    with memory.memory_graph(s) as M:
        tasks = experience(M, label_table)
    tasks = [t for t in tasks if len(t["steps"]) >= p["min_steps"]]
    by_id = {t["id"]: t for t in tasks}
    feats = {t["id"]: features(t) for t in tasks}
    pairs = []
    ids = sorted(by_id)
    for i, a in enumerate(ids):
        joined = False
        for b in ids[i + 1 :]:
            w = jaccard(feats[a], feats[b])
            if w >= p["similarity"]:
                pairs.append({"a": a, "b": b, "w": w})
                joined = True
        if not joined:
            pairs.append({"a": a, "b": None, "w": None})
    clusters = {x: [x] for x in ids}  # with no similar tasks at all, each is its own
    if any(r["b"] for r in pairs):
        with memory.memory_graph(s) as M:
            M.project_pairs("qlsc_tasks", pairs, labels=("Task",))
            clusters = M.leiden("qlsc_tasks", p["gamma"], p["seed"])
            M.drop_projection("qlsc_tasks")
    with memory.memory_graph(s) as M:
        existing = {k["key"]: k for k in M.rows(SKILLS)}
        names = {r["id"]: r["name"] for r in M.rows(COMPUTATION_NAMES)}
    llm = None
    for members in clusters.values():
        group = [by_id[x] for x in members if x in by_id]
        good = [t for t in group if success(t, p["negative"])]
        if len(group) < p["min_support"] or len(good) / len(group) < p["min_success"]:
            continue
        best = sorted(Counter(path(t) for t in good).items(), key=lambda x: (-x[1], x[0]))[0][0]
        key = hashlib.sha256(json.dumps(best).encode()).hexdigest()[:16]
        tables = sorted({r for t in group for r in t["reads"] if "." in r})
        procedure = [readable_step(fp, names) for fp in best]
        parameters = sorted({fp.split()[1].lower() for fp in best if fp.startswith("recall ")})
        if key in existing:
            k = existing[key]
            name, description, trigger, embedding = k["name"], k["description"], k["trigger"], k["embedding"]
        else:
            llm = llm or LLM(prompt("skill_system", **s.business), s)
            examples = sorted({mask(t["request"] or "") for t in group})[: p["examples"]]
            out = llm.call(
                prompt(
                    "skill_request",
                    support=len(group),
                    successes=len(good),
                    procedure="\n".join(f"{i}. {x}" for i, x in enumerate(procedure, 1)),
                    examples="\n".join(f"- {x}" for x in examples),
                ),
                NAME_SCHEMA,
            )
            name, description, trigger = out["name"], out["description"], out["trigger"]
            leaked = sorted(x for t in group for x in literals(t) if x in f"{name} {description} {trigger}")
            if leaked:  # never a value of the evidence in a shared skill
                continue
            embedding = embedder(s).embed([trigger])[0]
        with memory.memory_graph(s) as M:
            M.run(SKILL, key=key, id=str(uuid.uuid4()), version=1, now=now, owner=DISTILLER, name=name,
                  description=description, trigger=trigger, embedding=embedding, fingerprints=list(best),
                  procedure=procedure, parameters=parameters, tables=tables, support=len(group),
                  rate=round(len(good) / len(group), 3), evidence=[t["id"] for t in group])  # fmt: skip
            for old_key, old in existing.items():  # the same work, a different best path: an improvement
                if (
                    old_key != key
                    and old["status"] != "retired"
                    and len(set(old["evidence"]) & set(members)) * 2 >= len(old["evidence"])
                ):
                    M.run(SUPERSEDE, new=key, old=old_key)  # fmt: skip
    measure(s, now)
    with memory.memory_graph(s) as M:
        return M.rows(SKILLS)


def measure(s: Settings, now: dt.datetime) -> None:
    """The approved skills' uses and successes, from the tasks that followed them; an approved skill whose
    followers succeed too rarely is retired."""
    p = s["distill"]
    with memory.memory_graph(s) as M:
        skills = M.rows(SKILLS)
        tasks = {t["id"]: t for t in experience(M, model_tables(memory.reader_model(s, None)))}
        for k in skills:
            followers = [tasks[r["id"]] for r in M.rows(FOLLOWERS, id=k["id"]) if r["id"] in tasks]
            wins = sum(success(t, p["negative"]) for t in followers)
            M.run(STATS, id=k["id"], uses=len(followers), successes=wins)
            if len(followers) >= p["min_support"] and wins / len(followers) < p["retire_below"]:
                why = f"{wins} of {len(followers)} tasks that followed it succeeded"
                M.run(RETIRE, id=k["id"], fact=str(uuid.uuid4()), why=why, now=now, owner=DISTILLER)


def visible(m: memory.Model, skill: dict) -> bool:
    """A shared skill, as a reader may see it: only if they may read every table it is about, now."""
    return m.allow is None or all(m.allow.readable(t) for t in skill["tables"] or [])


def skills(s: Settings, m: memory.Model) -> list[dict]:
    """The skills this reader may see: without their evidence, only how much of it there is."""
    with memory.memory_graph(s) as M:
        try:
            rows = M.rows(SKILLS)
        except memory.DatabaseUnavailable:
            return []
    return [{k: v for k, v in x.items() if k not in ("evidence", "embedding")} | {"evidence": len(x["evidence"])}
            for x in rows if visible(m, x)]  # fmt: skip


def offers(s: Settings, m: memory.Model, request: str) -> list[dict]:
    """The approved skills to offer a new task: the closest by trigger to its request (masked), that the reader
    may see, at most distill.offers."""
    p = s["distill"]
    with memory.memory_graph(s) as M:
        try:
            approved = [k for k in M.rows(SKILLS) if k["status"] == "approved" and visible(m, k)]
        except memory.DatabaseUnavailable:
            return []
    if not approved:
        return []
    q = embedder(s).embed([mask(request)])[0]
    scored = sorted(((cosine(q, k["embedding"]), k) for k in approved), key=lambda x: -x[0])
    return [{"id": k["id"], "name": k["name"], "procedure": k["procedure"], "similarity": round(c, 3)}
            for c, k in scored[: p["offers"]] if c >= p["offer_similarity"]]  # fmt: skip


def followed(s: Settings, m: memory.Model, task: str) -> list[str]:
    """The approved skills a closed task followed: what it did and read close to theirs (the features tasks
    cluster by); -> their ids, recorded."""
    p = s["distill"]
    with memory.memory_graph(s) as M:
        try:
            approved = [k for k in M.rows(SKILLS) if k["status"] == "approved" and visible(m, k)]
        except memory.DatabaseUnavailable:
            return []
        if not approved:
            return []
        done = experience(M, model_tables(m), task)
        if not done or len(done[0]["steps"]) < p["min_steps"]:
            return []
        f = features(done[0])
        hits = [k["id"] for k in approved if jaccard(f, skill_features(k)) >= p["similarity"]]
        for k in hits:
            M.run(FOLLOW, task=task, skill=k)
    return hits


def approve(s: Settings, skill: str, as_: str | None) -> str:
    """A person approves a proposed skill: they must be able to read every table it is about."""
    m = memory.reader_model(s, as_)
    with memory.memory_graph(s) as M:
        k = next((x for x in M.rows(SKILLS) if x["id"] == skill or x["name"] == skill), None)
        if k is None:
            raise memory.Unsupported(f"no skill {skill!r}")
        if not visible(m, k):
            raise memory.Unsupported(
                f"{m.reader} may not read every table the skill is about, so may not approve it"
            )
        got = M.rows(APPROVE, id=k["id"], by=m.reader, fact=str(uuid.uuid4()), now=dt.datetime.now(dt.UTC))
    if not got:
        raise memory.Unsupported(f"skill {k['name']!r} is {k['status']}, not proposed")
    return got[0]["name"]


def show(rows: list[dict]) -> str:
    lines = []
    for k in rows:
        lines.append(f"{k['id']}  {k['name']}  [{k['status']}, v{k['version']}]  from {k['evidence'] if isinstance(k['evidence'], int) else len(k['evidence'])} tasks, {round(100 * (k['success_rate'] or 0))}% successful; used {k['uses']}, {k['successes']} successful")  # fmt: skip
        lines += [f"    {i}. {x}" for i, x in enumerate(k["procedure"] or [], 1)]
    return "\n".join(lines) or "no skills yet"


def run(
    s: Settings, approve_id: str | None = None, as_: str | None = None, distill_now: bool = False
) -> None:
    """qlsc distill, and qlsc skills [--approve ID] [--as PRINCIPAL]."""
    if distill_now:
        distill(s)
    if approve_id:
        print(f"approved: {approve(s, approve_id, as_)}")
    print(show(skills(s, memory.reader_model(s, as_))))
