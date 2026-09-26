# `qlsc ask --run` and `qlsc ask --cypher`

Status: done (2026-09-26); see Results.

## Why

`qlsc ask` goes from a question, through the semantic trace, to the cohort of tables that answer it, to
SQL, and stops at a dry run. Now that slice 1 has rows, a demo can go all the way to the answer. There
are two routes to it, and they should give the same answer:
- **SQL:** the SQL `ask` already writes, executed in the warehouse.
- **Cypher:** a query over the virtual graph that `qlsc virtualize` wrote from the same semantic layer.
  Virtual Graph turns it into SQL, and `EXPLAIN` shows that SQL.

## What changes

1. **`--run`** executes the query and prints the answer.
   - The SQL runs through the warehouse connector with a bytes-billed cap. A new optional connector
     method, `run(sql, maximum_bytes_billed)`, takes logical names and translates them like
     `dry_run`.
   - The Cypher runs on the Virtual Graph instance.
   - The cap and the number of rows printed are parameters in `defaults.yaml`
     (`navigate.maximum_bytes_billed`, `navigate.rows_shown`).
2. **`--cypher`** writes Cypher over the virtual graph instead of SQL.
   - **The model comes from the cohort.** The cohort's tables that are virtual-graph labels, plus the
     relationships that touch them (one hop), taken from `schema.json`, the model `virtualize` wrote and
     Virtual Graph loaded. If none of the cohort's tables is in the virtual graph, `ask` says so and
     stops.
   - **The log's evidence goes with it.** The same example queries as the SQL route, for definitions
     (flags, filters, date logic).
   - **The prompts** (`prompts/cypher_system.md`, `cypher_request.md`, `cypher_fix.md`) give the
     Virtual Graph Cypher subset as rules: start with `MATCH`; no `OPTIONAL MATCH`, variable-length
     paths, `CALL` subqueries or dynamic labels.
   - **The check is `EXPLAIN` on the Virtual Graph instance.** It rejects unsupported syntax, and its
     `External` operator holds the SQL Virtual Graph would send. A failed check goes back to the LLM
     once, like a failed dry run.
   - **Dates:** Virtual Graph has no `date()` or `duration()`, so the request carries today's date and
     the Cypher uses date literals. That's the date the SQL route's `CURRENT_DATE()` sees.
   - **No byte count for this route.** Virtual Graph sends the query's literals as `?` parameters, so
     its SQL can't be dry-run as it stands.
   - **Connection:** the Virtual Graph instance is `virtualize.neo4j` in the estate's config (uri,
     database). The password is `NEO4J_PASSWORD`, as for the semantic layer.

## What doesn't change

- Steps 1 to 4 (the semantic trace and the cohort) are identical for both routes, and deterministic.
- `ask` without flags behaves exactly as before.
- Nothing in the build or in the semantic layer changes, so there's no fingerprint change and the
  results stay as they are.

## Checks

- Unit tests for the model slice (the cohort's labels plus one hop) and for pulling the SQL out of a
  plan. The prompt test covers the new prompts.
- By hand, on the questions whose tables are filled and in the virtual graph (Q04, and the closure part
  of Q01): both routes return the same numbers, and match a hand-written query.

## Results (2026-09-26)

On the questions whose tables are filled:

| Question | SQL route | Cypher route |
|---|---|---|
| Q04 card spend by merchant category and segment, last quarter | 0 rows: the cohort missed `dim_customer`, and the SQL took segments from `sbx_customer_analytics.customer_360_final`, an unfilled `avoid` table | 45 rows, identical to a hand-written query |
| Q01 closures by site, and cost | 0 rows: reads `rpt_site_cost_per_contact`, which is empty until slice 2 | closures by site, correct (Tulsa 986, Manila 848, Spokane 614); says the costs are not in the graph |
| Q02 churn risk of high-balance customers | 0 rows: a sandbox copy (`customer_360_final_FIXED`) | not run: `customer_360` is not a label |
| Q05 month-end deposit balances by product line | the dry run fails twice (an ambiguous column), over a legacy table | not run: `fct_daily_account_balances` is not a label |
| Q12 affluent customers' contact details | 0 rows: filters `segment IN ('AFFLUENT', ...)`; the data says `affluent` | not run |
| Q14 closures by reason, deposits versus cards | totals right, split 0/0: filters `account_family = 'Deposits'`; the data says `DEPOSIT` | not run |

What this shows:
- **Values.** The SQL route guessed code values. The log already knows them: the `FILTERS` edges keep
  the literals each query ran with (`segment`: `affluent`, `private`; `account_family`: `DEPOSIT`;
  `customer_status`: `A`). Agreed and done (`navigate.filter_values`): each text column goes to the LLM
  with the values the log filters it on, in both routes.
  - Q12 now returns the affluent customers' contact details.
  - Q14 now splits closures into `CARD` and `DEPOSIT`, showing that each source has its own reason
    codes. It still counts distinct customers rather than closures (425 fraud closures against 441
    rows): the prompt's "count people by their identifier" rule, applied to events.
  - Q04's SQL still reads the unfilled sandbox copy.
- **Traps.** Where the cohort holds a sandbox or legacy copy, the SQL can pick it. Until slice 2 fills
  the `avoid` tables, a trap shows up as an empty answer rather than a wrong one.
- **The Cypher route is narrower but safer.** It can only use the virtual graph's labels, which leave
  out the suspect joins and the copies. So it answers correctly or says what's missing.
