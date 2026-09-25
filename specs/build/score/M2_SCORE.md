# M2 score: actor model, lifecycle and cost findings

Graph: Neo4j `semanticlayer`. Keys: the spec's service-account roles and teams; usage truth from `jobs_truth` (successful jobs only); planted findings from `answer_key.json`.

## Actor model

Principal class: **36 / 36** correct.

Teams (people grouped by what they consume): 8 inferred vs 10 in the spec; pairwise precision 61.1%, recall 100.0%, ARI 0.73.
- inferred team = digital_product + marketing_analytics
- inferred team = customer_analytics + data_science

Shape purpose: **1100 / 1100** successful shapes match the family that ran them (100.0%).

## Findings

| finding | result | detail |
|---|---|---|
| F19 The monitor touches everything | **pass** | elementary classed `monitor`; its traffic excluded from consumption (it alone would keep 32 unused tables looking alive) |
| F06 Dead tables | **pass** | 10/10 planted dead tables flagged unused; 93/93 of all flagged-unused tables confirmed unconsumed by usage truth; 92/92 of all tables usage truth says are unconsumed were flagged |
| F07 Written every night, read by nobody | **pass** | 3/3 planted write-only tables flagged; 29/29 write-only findings confirmed by usage truth |
| F11 Migration stragglers | **pass** | v2 stop date right; successor v3 named; stale Looker PDT flagged; 2 straggler findings in total |
| F05 Deprecated, and still load-bearing | **pass** | legacy table flagged; replacement named; chain to the Tableau report traced; 1 superseded findings in total |
| F09 Full scans of sharded and partitioned history | **pass** | 5/5 planted objects in 19 `unpruned_scan` findings |
| F20 LIMIT does not save money | **partial** | 2/3 planted objects in 10 `star_limit` findings (missed: dw_contact_center.fct_calls) |
| F21 Health checks that scan data | **pass** | 3/3 planted objects in 16 `probe_cost` findings |
| F22 Incremental models that rescan their source | **pass** | 4/4 planted objects in 8 `incremental_rescan` findings |
| F17 The code for "closure call" changed mid-window | **pass** | 'ACCT_CLOSE' on dw_contact_center.fct_calls.wrapup_code_name first filtered 2026-06-03; 1 drift findings in total |
