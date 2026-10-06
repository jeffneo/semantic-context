# What to take from alternate approaches: a plan for the elements worth integrating

Status: proposed (2026-10-05). Nothing here is built, and every item that changes the model or the method waits on your
decision (the last section).

## Why

We compared our approach with several alternate approaches to the same problem: giving agents governed, shared context about
an enterprise's data. On technique and on evidence ours is stronger. We infer the layer from usage. A typed request is compiled
by code instead of the model writing Cypher. The warehouse enforces access and is the oracle. And the measurements cover 186
questions.

But the alternatives cover ground we don't, and that ground is what a regulated buyer asks about: **how an agent reaches us,
what a data-use policy can stop before any query runs, which source is authoritative, and what a person has vouched for.** This
plan picks the few elements worth building, in order, and says what we are deliberately not taking.

## What the alternatives do that we don't

- **Hand-authored ontologies and metadata graphs**, with a person ratifying proposals. Ours is inferred, but we have no general place for
  what a person knows that no log can say.
- **Agents that write Cypher** over a metadata graph through a generic graph-database tool, from recipes in the prompt. Several
  model-written queries per question; the "budget" is a prompt rule, not a control.
- **An asserted reliability scale** (0 to 5, from a certified fixed report down to raw data in the prompt) attached to tools and data
  products as a label the model is asked to prefer. Nothing enforces it or tests it.
- **Asserted confidence scores** compared with an agent's minimum trust, and scores that "rise with each reuse" of an approved path.
  Nothing tests that a higher score is more correct.
- **A policy checked before the query runs**, which stops a correct query for the wrong purpose. This is the most persuasive thing
  they show, and our governance (the warehouse decides who may read which tables, columns and rows) has no concept of purpose.
- **A router drawn as a flowchart**: a near-match to an approved question reuses its template, a high-risk query needs human approval,
  otherwise Cypher is generated. It is our precedent, compiled and free routes in outline, without the measurement.
- **A conflict protocol**: two contradicting approved assets raise a flag and the agent escalates rather than choosing.
- **A restricted view for an external audience** by a secondary label and a database role.
- **An A/B design** with the same model and tools on both sides, repeated runs, and every warehouse call audited against the same
  policies. The largest gains reported are on governance and business-meaning questions, the types our comparison doesn't have.

Our own checks, for the plan: `llm.py` calls Anthropic only (lines 23 and 56), and embeddings go to Azure OpenAI. Fennmoor already has
deprecated-chain decoys (`legacy_edw.*`, finding F05 in `spec/questions.yaml`).

## The elements, in the order I'd build them

### 1. Evidence first: governance and business-meaning questions, repeated

Before building anything, add the measurement it will be judged by.
- **A governance set** (about 12 questions on Fennmoor): the same data asked for under an allowed and a forbidden purpose (for example
  customer-level contact data for a marketing use that the estate's policy bars), plus questions where the right answer is a refusal with
  the approved alternative.
- **A business-meaning set** where the definition is not in the log (a customer roll-up, which of two balance chains is the ratified one),
  with answers in the answer key.
- **Repeats.** Three runs per question in the new sets, reporting the spread. Our comparison is one run per question.
- **A violation audit run on both sides.** Every warehouse call of the baseline and of qlsc is checked against the same policies, the
  baseline after the fact and qlsc at run time. It is the number a regulated buyer reads.

Checked by: `eval/comparison/` gains the sets, and the report lists accuracy, tokens, seconds, silent-wrong and violations together,
with the new sets reported apart from the 186 so the old figures don't move.

### 2. Purpose and policy checked before any query (the gate)

What we have: the warehouse decides who may read which tables, columns and rows, and qlsc follows it. What we lack: a rule about
*purpose*. The warehouse can't know that a query is for rep coaching.
- A policy is a designed input, like a catalog: it **gates and annotates, never builds structure**, so it sits within our principle.
  Each says which tables, columns or Variables it covers, which purposes are barred, whether the effect is deny or mask, and who owns it.
- `qlsc ask --purpose <name>` (and the same field on a request through the delivery surface in item 3). The gateway checks the compiled
  plan against the policies **before** running it, and a barred plan returns the policy id, the reason, and the approved alternative the
  policy names. Every decision is written to the meter record.
- Where it lives: the estate's config names the policies, and the semantic layer shows them beside what they cover so a navigator sees them
  in context. Whether they are also nodes is decision 2.

Limits to state plainly: a purpose gate is **advisory against anything that does not go through qlsc**. The warehouse can't enforce it, so
it sits next to, and never replaces, the warehouse's own enforcement. Policies are declared by people. We don't infer them from usage.

Checked by: the governance set from item 1; zero violations on the audit for qlsc, a count for the baseline; `test_boundary.py` still
passing (no estate names in the tool).

### 3. Reach: an MCP server in front of the router

Agent frameworks commonly reach tools over MCP, and some deployments want "predefined methods rather than free-form text-to-Cypher". We
have a CLI and a Python library. Without an MCP surface, an agent framework can't call us at all.
- A **small read-only server** with a few predefined tools: `ask`, `recall`, `context` (what navigation finds for a question),
  `policies`, and `meter`. It is a surface over the existing router. It adds no new method.
- **Identity per request.** Alternatives make each agent a database user. Ours maps a caller's credential to a principal, and the
  **server signs** the virtual-graph queries for that principal. A generic graph-database MCP tool can't sign them.
- **What it refuses:** free-form Cypher against the virtual graph, as now.
- This is where the typed request pays off: the model fills a request instead of writing Cypher, which is the design these deployments ask for.

Checked by: an MCP-client agent running the converse conversations through the server and matching `eval/converse.py`; the entitlement
oracle run through the server for each principal; the meter figures the same as the CLI's.

This item depends on something outside our code: the LLM steps (the typed request and naming) run on Anthropic only, and a deployment may
route models through its own proxy. See decision 3.

### 4. Assurance level and a review gate on free SQL

The reliability scale's vocabulary is worth keeping, and "high-risk query → human approval" is a gate we lack. The place it fits is our
router, where the level is **measured and enforced**.
- Every answer carries an **assurance level** from the route that produced it, set in `defaults.yaml` with its reason: memory, a precedent,
  a compiled request, Cypher over the virtual graph, free SQL. The level is a property of the route and is never a number asserted per tool.
- **Free SQL, the last resort, is flagged for review** and, under `--as`, is returned as a proposal rather than run, unless the estate's config
  allows it. That is a change to the method (decision 4).
- We never put raw rows in the prompt, and the documents can say so in those words.

Checked by: the router tests assert the level for each route; a test that free SQL under a principal is not executed unless allowed.

### 5. Curation: authority, notes and ratification, which gate and annotate but never build

"Propose, then ratify" and attaching a confirmed tip to a table or column point at one thing we only half have. We infer, and we already
propose (alignment links, distilled skills) and a person approves skills. What's missing is a **small, general place for what a person
knows that no log can say**.
- **Status of a table.** Our computations already get stable, draft or deprecated from usage. Bring the same to tables (production, sandbox,
  frozen, deprecated chain), let a person ratify or override it with a reason, and use it in navigation and in the answer ("this uses the
  deprecated chain; use X").
- **Notes.** A short note attached to a table, column or Variable with who, when and confirmed or not (an undocumented status value, a case-sensitive
  argument, a landing time). Served with the context, confirmed first.
- Both are loaded from a file in the estate, never read by the build, and shown in the semantic layer's context. They are an annotation
  layer, not a source. The graph model stays small: properties, not a new node type (decision 5).

Checked by: Fennmoor's F05 decoy questions. The answer must name the deprecated chain, and a navigation run over seeds must not get worse (the
change adds a note, it doesn't re-rank).

### 6. A deployment profile that holds metadata only

Regulated reviewers accept a design more readily when the graph "holds metadata only". Our memory shard keeps row-derived context, and a
reviewer would notice the difference at once.
- Document what each shard holds, and make "semantic layer plus virtual graph, no remembered contexts" a **named, tested profile**. My
  understanding is that it is already separable, since memory is its own database and the memory route fires only when it holds the answer,
  but I haven't verified it. Add a `memory.enabled: false` setting that is read, and a test that nothing is written to the memory database with it off.

### 7. When knowledge conflicts: flag, don't pick

Today two approved skills, or a correction against a remembered answer, can disagree and we offer both or pick by similarity.
- Detect a conflict (same trigger, different approved outcome; a correction that contradicts a remembered answer) and mark it. The agent receives the
  flag and escalates instead of choosing.
- Smaller than the rest, and it needs real conflicts to test: seed them in the distillation simulation.

### 8. A per-audience view of the semantic layer, done more strictly

A restricted view matters when client agents are to see only a subgraph. Take the idea, not the usual construction.
- An **allowlist** of properties instead of a denylist, a view per audience (a database or composite constituent each) instead of one shared
  label, and the procedures that list names (relationship types, property keys) probed as part of the test, since a label-restricted role can
  still see those lists.
- Probed the way `memory_entitlements.py` probes memory: as the restricted user, against what the warehouse would show.

Lower priority: it protects metadata, and the warehouse already protects the rows.

## What we are deliberately not taking

- **Asserted reliability and confidence scores.** They are numbers someone typed, and nothing tests that a higher one is more correct. Our levels
  come from the route, and our freshness and trust from measurements.
- **A hand-authored ontology as a source.** It conflicts with usage as ground truth. A designed model is aligned afterwards.
- **Free-form Cypher with prompt recipes** as the way an agent reaches data, for the cost and control reasons above.
- **Label-based role access as the security boundary** (a denylist on one shared label).
- **Build-time readiness tracking** (no API yet, vendor feed pending). It matters for a registry of tools and doesn't arise with a warehouse that is
  always readable. It becomes relevant only if we add tool or API sources.
- **Loading the data into the graph** as a default. Our zero-copy virtual graph is the point of difference.

## Phases

0. **Ask before building** (no code): which agent runtime and MCP server version the first deployment uses, and which LLMs its proxy allows.
1. **Item 1,** the evidence sets, with the audit. This is cheap, it can run against the current system to show where it stands, and it fixes the target.
2. **Item 2,** the gate, measured on item 1's sets.
3. **Item 3,** the MCP server, with policies and meter exposed.
4. **Items 4, 5 and 6** in either order. Each is small.
5. **Items 7 and 8** after the delivery surface exists.

Each item that changes results reruns the example's evaluations, updates `results/`, and moves what stays true into `docs/design.md` (CLAUDE.md's
rule). The existing 186-question figures must not move.

## Decisions I need from you

1. **Are policies in scope?** They are a designed input that gates and never builds. I recommend yes, with an explicit "advisory beyond qlsc" statement.
2. **Config only, or nodes in the semantic layer?** I recommend config as the source and one property or node set on what a policy covers, so
   navigation shows it, and no new label until a query needs one.
3. **LLM portability.** The typed request and naming run on Anthropic only, so a runtime that allows another model only couldn't use the compiler.
   Options: leave it (the server calls us and we call Anthropic), or put a provider seam in `llm.py` now. I recommend leaving it, and measuring before
   we claim any other model.
4. **Free SQL under a principal: run, or return as a proposal?** I recommend a proposal by default, runnable when the estate allows. It changes a
   router behaviour, so it is yours to decide.
5. **Curation as properties, not a node type.** Consistent with keeping the graph small. I recommend properties until the notes need relationships.
6. **Order.** Items 1 to 3 first, as above, or the MCP server first because it unblocks a runtime that can't call us at all?

## Risks

- A purpose gate suggests more protection than it gives. The wording must say what it covers.
- The governance and meaning sets are written by us, from our own policies, so the result shows the gate works, not that the policies are right.
- The MCP surface adds a second place where identity can go wrong; the oracle test through the server is what answers that.
- Everything here is measured on one synthetic estate.
