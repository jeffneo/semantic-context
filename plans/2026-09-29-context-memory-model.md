# Context Memory: a model for the agent's side of memory

Status: agreed (2026-09-29), with the recommendations below taken on every open item; built the same day
(see "As built" at the end). It replaces the agent side of [the memory plan](2026-09-27-agentic-memory.md)
(phase 3, first built on Neo4j Labs' agent-memory). The warehouse side stays: remembered rows, freshness
and entitlements (phases 1 and 2), now with `READ` edges in place of per-principal properties (decision 4).

## Why

**agent-memory is giving way to Context Memory.** Context Memory is a graph-native memory layer for agents,
with short-term, long-term and reasoning memory. Its differentiator is skill distillation:
- **decision tracking:** a permanent record of the agents' reasoning and operational paths;
- **knowledge distillation:** graph algorithms condense repeated events into reusable knowledge;
- **continuous improvement:** what's learned feeds back into the system and refines future reasoning.

**What agent-memory got right, and this keeps:**
- **Three layers joined by edges that mean something.** A message mentions what it's about, reasoning
  starts from a message, and a step records what it touched.
- **An ordered message chain.**
- **An auditable reasoning record:** each step with its status and duration.
- **Two kinds of time on facts:** when it was recorded, and when it held.
- **Deduplication** by `SAME_AS`, and embeddings on text for retrieval.

**Where it falls short, and this fixes** (the review of 2026-09-29):
- **Housekeeping labels:** `Extractor` and `Schema`.
- **Two nodes per tool call:** `ReasoningStep` and `ToolCall`.
- **Shortcut links that repeat a path:** `TRIGGERED_BY`, `HAS_TRACE` and `FIRST_MESSAGE`.
- **Facts are strings,** with no link to what they're about.
- **Time only on facts:** nothing marks what replaced what.
- **A generic `Entity` copy** of what the domain already holds. Its POLE+O labels collide with domain labels,
  and the labels made at run time can multiply without limit.
- **No owner or visibility,** except a user id on the conversation.
- **Important fields buried in JSON text.**
- **No decisions, and no distillation:** the two things the mandate is about.

## Principles

1. **Few labels.** Each is a plain word a business reader uses. Evidence goes on properties.
2. **The enterprise's own nodes are the long-term memory.** A message mentions the `Customer` the warehouse
   holds, not a copy of it.
3. **One relationship type per meaning,** reused across labels: `PART_OF`, `FROM`, `ABOUT`, and so on.
4. **Nothing is edited or deleted in the normal course.** A change is a new node that supersedes the old.
5. **Security is part of the model.** Every node says whose it is and what it came from.
6. **Experience is the ground truth.** Skills and distilled knowledge are inferred from what the agents did
   and how it turned out, as qlsc infers the semantic layer from the query log.

## The model

**Labels.** Eight on the agent's side, plus the domain's own and the layer's stubs.

| label | what it is | key properties |
|---|---|---|
| `Conversation` | a session between a principal and one or more agents | title, started_at, ended_at, owner |
| `Message` | one turn | seq, role (user, agent), agent, text, at, origin, owner |
| `Task` | one request an agent worked on: the unit of experience | request, status (done, failed, abandoned), started_at, ended_at, owner |
| `Step` | one action in a task: a tool call, or a thought | seq, agent, tool, arguments, result (a summary), status (ok, error, refused), duration_ms, fingerprint, at, owner |
| `Decision` | a choice made, and why | choice, rationale, alternatives, decided_by (an agent or a person), valid_from, valid_until, owner, scope |
| `Fact` | a statement: a preference, a relation, an outcome, a rating, an approval, a distilled pattern | predicate, value, origin (said, observed, inferred, distilled), confidence, valid_from, valid_until, status, owner, scope |
| `Entity` | a person or thing no domain label holds | name, type (person, organization, place, event, thing), owner |
| `Skill` | a reusable procedure distilled from repeated, successful tasks | name, description, trigger, procedure, parameters, status (proposed, approved, retired), version, uses, successes, scope |
| the domain's: `Customer`, `Account`, … | the warehouse's rows, remembered (phases 1 and 2) | source, its key, fetched_at, holds_until |
| stubs: `Table`, `Column`, `Computation` | the semantic layer's nodes, by an id that survives a rebuild | id, name |

Every node also has `recorded_at`, when memory learned it, which never changes. Text-bearing nodes
(`Message`, `Task`, `Fact`, `Skill`) carry an embedding for retrieval.

**Relationship types.** Ten, plus the domain's own and the stubs' `HAS_COLUMN`.

| type | from → to | meaning |
|---|---|---|
| `PART_OF` | Message, Task → Conversation; Step, Decision → Task | containment |
| `NEXT` | Message → Message; Step → Step | order (`seq` too: the first is 1) |
| `FROM` | Task → Message; Fact → Message or Step; Skill and a distilled Fact → Task or Decision; a domain node → Table | where it came from: provenance, one type everywhere |
| `READ` | Step → whatever it read: domain nodes, Table, Computation, Fact, Skill, Decision | what the agent looked at |
| `ABOUT` | Fact, Decision → its subject; Skill → the stubs it works over | what it's about |
| `MENTIONS` | Message, Fact → anything else it names | references |
| `BASED_ON` | Decision → Fact, Step, domain node, or an earlier Decision (a precedent) | why |
| `SUPERSEDES` | Fact, Decision, Skill → the one it replaces, `{because: changed, corrected, reversed, improved}` | nothing is deleted |
| `SAME_AS` | Entity → a domain node or another Entity | resolution |
| `FOLLOWED` | Task → Skill | the feedback loop |

## An example: the two marketing sessions

```
(conv:Conversation {title: "Card offer for customer 8322…", owner: "marketing"})
(m1:Message {seq: 1, role: "user", text: "I'm meeting customer 8322… today…"})-[:PART_OF]->(conv)
(m1)-[:MENTIONS]->(c:Customer {customer_key: 8322…})            // the remembered row itself
(t1:Task {request: "What do we hold for them?"})-[:PART_OF]->(conv),  (t1)-[:FROM]->(m1)
(s1:Step {seq: 1, tool: "recall", fingerprint: "recall Customer ?"})-[:PART_OF]->(t1)
(s1)-[:READ {holds_until: …}]->(c)
(s2:Step {tool: "ask", fingerprint: "ask card spend by merchant category, for a Customer, over a quarter"})
(s2)-[:READ]->(:Table {id: "…fct_card_transactions"}),  (s2)-[:READ]->(:Computation {id: "ddb14…"})
(f1:Fact {predicate: "prefers contact channel", value: "email, not phone", origin: "said"})
(f1)-[:ABOUT]->(c),  (f1)-[:FROM]->(m5)
(ana:Entity {name: "Ana", type: "person"})
(f2:Fact {predicate: "daughter of"})-[:ABOUT]->(ana),  (f2)-[:MENTIONS]->(c)
(d1:Decision {choice: "offer a travel rewards card, by email", rationale: "asked about travel; prefers email"})
(d1)-[:ABOUT]->(c),  (d1)-[:BASED_ON]->(f1),  (d1)-[:BASED_ON]->(s2)

// session 2
(f3:Fact {predicate: "prefers contact channel", value: "phone, mornings"})-[:SUPERSEDES {because: "changed"}]->(f1)
(o1:Fact {predicate: "outcome", value: "accepted"})-[:ABOUT]->(d1),  (o1)-[:FROM]->(m…)

// distilled later, from many such tasks
(k:Skill {name: "Prepare for a customer meeting", status: "approved",
          procedure: ["recall Customer {customer}", "ask card spend by merchant category for {customer}, last quarter"]})
(k)-[:FROM]->(t1), (k)-[:FROM]->(…),  (k)-[:ABOUT]->(:Table {id: "…dim_customer"})
(t9:Task)-[:FOLLOWED]->(k)
```

`d1` was based on a preference that session 2 superseded. `MATCH (d:Decision)-[:BASED_ON]->(:Fact)<-[:SUPERSEDES]-()`
finds it: the offer's channel needs revisiting.

## Time

Two kinds of time, as agent-memory's facts had and Graphiti does:
- `recorded_at`: when memory learned it. It never changes.
- `valid_from` and `valid_until` on facts and decisions: when it held in the world.

**A replacement says why.** `SUPERSEDES {because: changed}` means the world changed: the old fact was true,
and its `valid_until` is set. `{because: corrected}` means memory was wrong: the old fact never held. The
audit trail needs the difference.

**Feedback is facts.** Outcomes, ratings, corrections and approvals are Facts about a Task, Decision or
Skill, so they have provenance and time like anything else. Continuous improvement reads them.

**Warehouse facts keep their freshness** (`fetched_at`, `holds_until`, from each table's write cadence), as
built.

## Security

1. **Identity comes from the gateway, never from content.** `owner` is the principal the conversation
   acts for, taken from the signed token (phase 3 of the entitlements plan). An agent or a message can't
   set it.
2. **Every node has an owner and a scope.** `scope` is `private` (the owner only) or `shared`. Everything
   recorded in a conversation is private.
3. **Sharing is an act, recorded.** Only distilled knowledge (Skills, distilled Facts) becomes shared,
   through a person's approval, which is itself a Fact (`predicate: approved`, `FROM` who approved it).
4. **Shared knowledge carries no values.** Distillation fingerprints steps the way the parser fingerprints
   SQL: literals out, parameters in (`recall Customer {customer}`). So shared knowledge is schema-level,
   and its lineage stops at Table and Column stubs, not rows. Its evidence (the tasks it came `FROM`)
   stays private: another reader sees how many tasks it came from, not which.
5. **Reads follow lineage.** A reader sees a node if it's theirs, or if it's shared and they may read
   everything it came `FROM` now, down to the warehouse's tables and columns. The gateway checks it at read
   time, the way navigation shows an example only if every table and column it reads is readable.
6. **A row-policied warehouse fact** is visible to a principal whose own step read it, while that read
   holds: `(:Step {owner})-[:READ {holds_until}]->(fact)`. This replaces phase 2's per-principal property
   names: the context record is the recall step itself, and every read leaves a record (decision 4).
7. **Content is data, not instructions.** `origin` says who said a thing: a user, an agent, a tool, or a
   person who approved it. Text from people and tools is never offered to an agent as guidance. Only
   approved skills and facts are. That is the defense against memory poisoning.
8. **Search never ranks what you can't see.** Vector search filters by owner and scope before it ranks,
   because an embedding is as sensitive as its text.
9. **Nothing is edited.** Steps and decisions are append-only. An optional digest chain per task (each
   step's hash over the one before) makes the record tamper-evident.
10. **Erasure by lineage.** Forgetting a customer follows `ABOUT`, `MENTIONS` and `READ`: it redacts message
    text and removes facts about them. Shared knowledge holds no values, so it survives intact. Retention is
    by policy per label (`retain_until`): conversation text for months, decisions for years.
11. **Defense in depth.** Memory is a standard database, unlike the virtual graph, so Neo4j's
    property-based access control could enforce `owner` and `scope` in the database too. To be verified
    here: it needs a role per principal.

## Distillation and continuous improvement

**The same method qlsc uses on the warehouse's log, applied to the agents' own record:**

| qlsc, from the query log | Context Memory, from the agents' experience |
|---|---|
| a query, fingerprinted (literals out): a QueryShape | a step, fingerprinted; a task's path of them |
| shapes clustered by Leiden: Semantic areas | tasks clustered by what they did and read: kinds of work |
| repeated expressions: Computations, trusted by production use | repeated successful paths: Skills, approved by a person |
| navigation offers a question its tables and examples | memory offers a task its closest skills and precedents |
| accuracy measured on held-out questions | a skill's value measured: tasks that followed it against those that didn't |

**The loop:**
1. **Record.**
   - Tasks, fingerprinted steps, decisions, and outcomes as facts.
   - An ask's fingerprint is its compiled request without its values: its measures, groupings and filter
     shapes.
2. **Cluster.**
   - Exact repeats of a task's step path first.
   - Then a similarity graph of tasks: shared step fingerprints, shared tables and labels read, and
     request embeddings. Leiden runs over it, seeded and deterministic, as qlsc's builds are.
3. **Distill.**
   - From each cluster with enough successful tasks, a proposed Skill. Its procedure is the most common
     successful path, with its literals as parameters. Its name and trigger come from an LLM, over the
     cluster's requests (a prompt in `prompts/`), as qlsc names its groups.
   - From clusters of decisions (similar subjects and evidence, known outcomes), proposed distilled Facts,
     for example "for travel card offers to mass-segment customers, email beats phone: 14 of 20
     accepted".
4. **Approve.** A person reviews. Approved means shared, and fed back.
5. **Offer.** At a new task, the closest approved skills, and precedent decisions about what the task
   mentions: by trigger embedding, and by graph proximity to the mentioned nodes. `FOLLOWED` records use.
6. **Measure.** Outcome facts of tasks that followed a skill against those that didn't: the skill's
   `uses` and `successes`.
7. **Revise.** A skill that stops working is retired. A better path supersedes it
   (`SUPERSEDES {because: improved}`).
8. **Feed the core system.**
   - A corrected answer becomes a test case for qlsc's quick tests.
   - The agents' asks reach the semantic layer through the warehouse's own query log, labelled, so a
     build can weigh or exclude them (decision 5).

## What changes from agent-memory

| agent-memory | Context Memory |
|---|---|
| `Conversation`, `Message` | kept |
| `HAS_MESSAGE`, `FIRST_MESSAGE`, `NEXT_MESSAGE` | `PART_OF`, `NEXT`, and `seq` |
| `ReasoningTrace` | `Task` |
| `ReasoningStep`, `ToolCall`, `Tool` | `Step` (the tool a property; a tool's counts an aggregate) |
| `HAS_TRACE`, `HAS_STEP`, `USES_TOOL`, `INSTANCE_OF`, `TRIGGERED_BY`, `INITIATED_BY` | `PART_OF`, `NEXT`, `FROM` |
| `TOUCHED` | `READ` |
| `Preference`, `Fact` | `Fact` (a preference is a fact whose predicate says so) |
| `RELATED_TO` | a `Fact` `ABOUT` one thing that `MENTIONS` the other |
| `Entity` with POLE+O and subtype labels | the domain's own nodes; `Entity {type}` only for what none holds; no labels made at run time |
| `SAME_AS`, `ABOUT` | kept (`ABOUT` from Fact, Decision and Skill) |
| `EXTRACTED_FROM` | `FROM` |
| `EXTRACTED_BY`, `Extractor`, `Schema` | gone: how a fact was extracted is a property of it |
| none | `Decision`, `Skill`; `BASED_ON`, `SUPERSEDES`, `FOLLOWED`; owner, scope, origin and status; recorded_at with validity |

## What changes in qlsc, if agreed

- **`qlsc/converse.py`** is rewritten on this model, and `eval/converse.py` adapted: the same checks, plus
  decisions, outcomes and why a fact was superseded.
- **Phase 2's per-principal property names** (`context_*:<principal>`, `seen_until:<principal>`) become
  `READ` edges from recall steps (decision 4).
- **Distillation is new work,** a phase of its own: fingerprints, clustering, naming, approval, offering
  and measurement.

## Decisions (2026-09-29: the recommendations, taken)

1. One `Fact` label: yes.
2. Decisions are private to their owner by default; shared only through approval.
3. A person approves a skill before it's offered: yes.
4. `READ` edges from recall steps replace phase 2's per-principal properties: yes.
5. The agents' queries don't feed the semantic layer yet. The estate's log is a synthetic stand-in table
   (`fnb_query_log.jobs`), so they don't reach it today. When they would, they're labelled, so a build
   can weigh or exclude them.
6. Names: `Task`, `Entity`, `Fact`.
7. Order: the agent side on this model, then distillation (memory phase 4), then the memory route and the
   economics (memory phase 5).

## Decisions as first put

1. **One `Fact` label** for preferences, relations, outcomes, ratings, approvals and distilled patterns,
   rather than `Preference` and `Fact`.
2. **Who sees a decision:**
   - private to its owner (my default), shared only through approval; or
   - an enterprise record, visible to anyone who may read its evidence.
3. **A person approves** a skill or a distilled fact before it's fed back. I recommend yes, as the defense
   against memory poisoning.
4. **`READ` edges from recall steps** in place of phase 2's per-principal properties. It reworks built
   code, and it's cleaner and auditable.
5. **The agents' asks reaching the semantic layer through the query log.** Usage is the ground truth, but
   an agent learning from its own queries needs care.
6. **Names:** `Task` (or `Episode`), `Entity` (or `Party`, or `Thing`), `Fact` (or `Note`).
7. **Order:**
   - rebuild the agent side on this model;
   - then distillation, the differentiator;
   - then phase 4's memory route and economics.

## As built (2026-09-29)

**The agent side** (`src/qlsc/converse.py`, `qlsc converse <file> [--as]`):
- **The model as drafted:** the labels `Conversation`, `Message`, `Task`, `Step`, `Decision`, `Fact`, `Entity`
  and `Skill`, with every node carrying `owner`, `scope` and `recorded_at`.
  - **The relationship types written:** `PART_OF`, `NEXT`, `FROM`, `READ`, `ABOUT`, `MENTIONS`, `BASED_ON`,
    `SUPERSEDES` and `FOLLOWED`.
  - **Tasks and steps.** Each user message starts a Task, `FROM` it, and the agent's reply closes it.
    A recall's Step is memory's own. An ask's Step keeps its route, query and first rows, and `READ`s
    the Table and Computation stubs.
  - **Facts and decisions.** Facts are `{predicate, value}` `ABOUT` a subject, and `MENTIONS` anything else
    they name. Decisions are `BASED_ON` facts and steps. Outcomes and ratings are Facts about a decision
    or a task.
  - **Supersession** is `{because: changed}` (the old fact held until now) or `{because: corrected}` (it
    never held). `qlsc recall` flags a decision based on a superseded fact: "revisit: …".
  - **Not written yet: `SAME_AS`.** Resolving an Entity to a warehouse node needs entity resolution,
    which isn't built.
- **Owner comes from the gateway,** never from content. `Conversation.run` binds `$by` to the reader
  on every statement, so the agent side can't write another owner's nodes.
- **The example conversations** are in the new format: facts in place of preferences, a decision, an
  outcome, and a risk decision.

**The warehouse side, reworked (decision 4):**
- **Every recall is a Step its reader owns,** from memory too. That's the record of who read what, and
  when.
- **A fetch's step `READ`s the anchor,** the context record: its template, and until when it holds.
- **It also `READ`s every row-policied node it fetched** (`holds_until`). Such a node is read from memory
  only by a principal whose own step read it and still holds. A relationship is read only between
  nodes the reader may see.
- **The per-principal properties are gone:** `seen_until:<principal>` and `context_*:<principal>`, cleared
  from memory, along with agent-memory's 38 nodes and its constraints.
- **Pruning on refetch.** A refetch removes a relationship it didn't return only where it could have:
  not one whose other end is row-policied and unseen by the reader.
- **A record dated after the reading clock doesn't count yet** (`s.at <= $now`). A freshness check that
  moved the clock forward had left one that still held.

**Distillation** (`src/qlsc/distill.py`, `qlsc distill`, `qlsc skills [--approve ID] [--as]`):
- **Tasks.** Distillation uses tasks of `distill.min_steps` (2) or more. A task succeeds if it closed,
  every step ran, and no rating or outcome in `distill.negative` came back.
- **Clusters.** Tasks are joined by Jaccard similarity (at least `distill.similarity`) over their step
  fingerprints and the tables they read, then clustered with seeded, single-threaded Leiden through
  GDS on the memory database. `Graph.project_pairs` now takes the labels to project; its default
  matches the build's nodes exactly (4,128 of 4,128, checked).
- **Proposed skills.** A cluster of `min_support` (3) tasks or more, at least `min_success` (70%) of them
  successful, becomes a proposed Skill:
  - its procedure is the most common successful path, written from the fingerprints: schema only, with
    Computations by name;
  - its name, description and trigger come from the LLM (`prompts/skill_*.md`), given masked requests,
    and are checked against every literal of the evidence;
  - a skill's identity is a digest of its procedure, so distilling again updates it. A different best
    path over the same evidence supersedes it (`because: improved`).
- **Approval.** A person approves a skill, and must be able to read every table it's about. The approval
  is a Fact about the skill.
- **Offers.** An approved skill is offered at the start of a task whose masked request is close to its
  trigger (cosine at least `offer_similarity`), only to readers who may read all its tables. The offers
  are recorded on the task (`offered`).
- **Measurement.** A task whose steps and reads are close to an approved skill's `FOLLOWED` it. A skill's
  uses and successes count its followers, and it's retired, with a Fact about it, when they succeed
  less than `retire_below`.
- **Evidence stays private.** Readers see how many tasks a skill came from, not which.

**Checked:**
- `eval/converse.py`: 26 of 26.
- `eval/distill.py`: 13 of 13, over a simulated record:
  - marketing's meeting preparation, repeated 5 times, and risk's review, 4 times, both rated helpful;
  - a pattern repeated 3 times and rated wrong;
  - two one-offs.

  The distilled skills:

  | skill | from | procedure |
  |---|---|---|
  | Review customer holdings and recent card spending | 5 marketing tasks, all successful | recall the Customer's context; ask Card Purchase Spend (a Computation) by merchant category group, for the customer, over a period |
  | Review customer risk and deposit activity | 4 risk tasks, all successful | recall the Customer's context; ask the sum of deposit amounts by transaction type, for the customer, over the quarter |

  - **Nothing else.** The failing pattern and the one-offs gave no skill, and no customer key appears in
    either skill.
  - **Approval.** Contact-center may not approve the risk skill. Marketing approves its own, once.
  - **Offers.** A new request like marketing's is offered its skill (cosine 0.75). Contact-center's same
    request is offered nothing. The proposed risk skill is offered to no one.
  - **Measurement.** Two new sessions follow the skill and succeed (used 2, 2 successful). Two more
    follow it and are rated wrong, and the next distillation retires it: "2 of 4 tasks that followed it
    succeeded".
