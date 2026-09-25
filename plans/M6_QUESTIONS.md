# M6: answering questions with the semantic layer, and views

Status: complete, 2026-09-24. Parent plan: [PIPELINE_PLAN.md](PIPELINE_PLAN.md) (Stage 7).

Code:
- `pipeline/guide.py`: table status and "use instead" links.
- `pipeline/tools.py`: the agent tools.
- `pipeline/answer.py`: the agent.
- `pipeline/views.py`: the Enterprise Studio perspective.

Scorer: `specs/tools/score.py` (M6 section, `--only-m6`). Output: `specs/build/score/M6_SCORE.md`.

## What was built

**1. Guidance (`guide.py`).** Every table gets a status (current, caution or avoid), the evidence behind it, and
where it applies a `USE_INSTEAD` link. It is a reading of earlier findings, not new inference:

| Status | Comes from |
|---|---|
| avoid | nobody uses it (M2 dead); frozen; a superseded legacy chain → its replacement; writer stopped → its successor; a hand-made copy → its original; built through a suspect join; a column in dollars computed from cents |
| caution | maintained by a person, not by production; a raw feed that production models into a mart → that mart (the one carrying most of its columns); written but never read; BI-generated; restricted dataset; raw sensitive values; an alternative to the sanctioned measure |

*Frozen vs. live* comes from the log alone. Some tables have no write jobs, such as CDC streams or the Storage Write
API. If production builds keep reading such a table (directly or through a view) in the last two weeks, it is
live. If not, nothing depends on it being current, so it is frozen.

Tables also carry `:Avoid` / `:Caution` labels for colouring, and `(:Table)-[:JOINS]` table-level join summaries
for exploring. The column-level JoinKeys remain the evidence.

**2. Tools (`tools.py`).** Nine functions over the graph plus BigQuery's planner. They could back an MCP server as
they stand:

| Tool | What it does |
|---|---|
| `search_tables` | M5 retrieval; each hit carries its status and alternative |
| `find_tables_by_name` | name search, for questions about names (Q13) |
| `describe_table` | columns with variables; how the business filters it (and on which values); what it joins with; how it is built (the production SQL); its sources with date coverage from shard names; findings |
| `join_path` | Steiner-style path over joins the business runs. Production joins are weighted first, then corroborated, then single. It falls back to "same variable on both sides" and penalises avoid tables. Joins production contradicts are listed under `do_not_join` |
| `example_queries` | SQL the business already runs against these tables, ranked by production first, then how many principals run it. Queries through suspect joins are dropped. This is the log as institutional memory: the delinquency rate query 3 analysts run with open loans as the denominator, and the fraud build that treats "no case" as not confirmed |
| `sensitive_data` | every SSN / tax-id column: raw or hashed (by lineage or by name), restricted or not, exposure findings |
| `find_columns` | variables found by meaning or name |
| `column_detail` | a column's lineage and the values it is filtered on, with dates (codes drift) |
| `dry_run` | rewrites logical names to the deployed ones, runs BigQuery's free dry run, and reports the status of every table the SQL reads |

**3. The agent (`answer.py`).**
- **Model:** Haiku (`qa.model` in estate.yaml, D4: speed).
- **Instructions:** check a table before relying on it, follow status and use-instead, take joins from
  `join_path`, reuse the business's own definitions, filter as the business does, and say what the evidence cannot
  tell.
- **Output:** tables, joins, SQL, warnings, avoided traps, and what the evidence cannot tell.
- **Checks on the final answer:**
  - the SQL is dry-run again;
  - every listed table must resolve to a real table (this catches invented names and malformed output);
  - a failure goes back to the model for up to two fixes.
- **Cache:** every call is cached by its full request.

**4. Baseline.** The same model, prompt skeleton and loop, but with only what BigQuery's catalog gives: names,
columns, types, partitioning and dry runs.

**5. Views (`views.py`).**
- **Perspective:** `pipeline/views/semantic-layer.perspective.json`, in the export format of real Bloom perspective
  files (version 2.3.0). Import it in Explore via Perspective drawer → Import.
  - Tables are coloured by status; subjects and domains form the map.
  - 12 search phrases: semantic map, table neighbourhood, join A to B, lineage, who uses it, traps, variable,
    customer identity, sensitive data, suspect joins, copies, findings.
  - Each phrase is executed with a sample parameter before the file is written.
- **Cypher:** the same queries in `cypher/views.cypher`.

## Score (3 independent runs per mode, mean and range)

| | semantic layer | catalog only |
|---|---|---|
| questions fully right (every expected table, no trap, no wrong join, valid SQL) | **12.7 / 14** (12–13) | 9.3 / 14 (9–10) |
| expected-table recall | **95%** | 79% |
| trap tables used (26 in the key) | **0** | 1 (the April email extract, every run) |
| joins between different id spaces | 0 | 0.3 |
| SQL that dry-runs clean | 12 / 12 | 12 / 12 |
| must-handle items (judged by `claude-sonnet-5`; pass 1, partial 0.5) | **69%** (62–81%) | 26% (16–32%) |

**F18 (negative control): pass.** Ledger double counting needs domain knowledge.
- No finding claims it.
- The `limits` finding says it is not determinable from usage.
- No Q01 answer adds `gl_erp.vendor_invoice`.

Cost of a full 3×2 scoring from scratch: about $5 of agent calls plus the judge. One question costs about $0.08
and takes 30 s.

## What the numbers say

- **Tables.** On this estate, catalog-only is stronger than expected. The warehouse is well named (`dw_core.fct_*`),
  so an agent that lists tables finds the marts. It falls down where names mislead or say nothing:
  - Q06: where SSNs live under other names;
  - Q09: the open-loan denominator in `dim_account`;
  - Q12: it picks the stale April email list every time.
- **Must-handle items.** This is where the semantic layer earns its keep (69% vs 26%). The difference is knowledge
  that is only in the log:
  - how production builds a measure;
  - which denominator the analysts use;
  - which codes are filtered on, and since when;
  - which identity path the business uses.

## Known misses

- **Q01 (0/3 both modes).** 2025 volume needs `fct_contacts_all`, the union of Genesys and legacy Avaya. The
  evidence is in the graph:
  - `fct_contacts_all`'s view definition;
  - the `cdr_*` shards ending 2025-09;
  - "feeds" on `fct_calls`.

  The agent still reaches for `fct_calls`. Agent-site vs queue-site attribution is visible in `site_id`'s lineage
  (`COALESCE(agent site, queue site)`) but is never stated. Two remedies are possible: a **coverage** finding
  ("this table's sources start at X"), which needs the first date of data (profiling, outside D1); or a stronger
  model.
- **Q03, Q14 (partial).**
  - Q03: the business resolves GA4 identities before `fct_web_sessions`, so answers join on `customer_key`. That is
    correct, but the judge wants the path named.
  - Q14: answers note that card and deposit reason codes differ, but do not map them. The log has no query that
    maps them.
- **Q06.** The single `sensitive_data` call finds all five raw locations. Answers sometimes drop the restricted
  `aml_kyc.party` because it is "protected".

## Operational note

`topology.py` rebuilds Subject nodes, which removes M5's names, embeddings and domain links. `run.sh` reruns
`semantics.py` after it (cached, free). This bit M6 once and was caught when the "semantic map" view came back empty.
