# Memory's entitlements, with the warehouse as the oracle

Check 4 of plans/2026-09-27-agentic-memory.md (phase 2): memory never shows a reader more than BigQuery, queried as that reader, would. The data source remembers every anchor first, so memory holds every row; each principal then remembers and recalls them as themselves (`--as`). Every context read back from memory is checked against BigQuery read as the principal directly: each node a row they may read, with the same values; each relationship the foreign key in that row; no hidden column; no table they can't read.

**0 incidents** in 18 recalls; 0 differed from the principal's own fetch.

| principal | anchor | nodes | relationships | same as their fetch | verdict |
|---|---|---|---|---|---|
| marketing | Customer -9222608688654483010 | 187 | 278 | yes | ok |
| marketing | Customer -9218325325162838369 | 1 | 0 | yes | ok |
| marketing | Customer 4406449607907749601 | 658 | 1283 | yes | ok |
| marketing | Customer 8322097816940277129 | 640 | 1250 | yes | ok |
| marketing | Branch 101 | 931 | 1189 | yes | ok |
| marketing | Agent 9143e7f7-8e11-6904-c98e-fb076ea611a1 |  |  |  | refused |
| risk | Customer -9222608688654483010 | 187 | 278 | yes | ok |
| risk | Customer -9218325325162838369 | 1 | 0 | yes | ok |
| risk | Customer 4406449607907749601 | 0 |  |  | nothing they may read |
| risk | Customer 8322097816940277129 | 0 |  |  | nothing they may read |
| risk | Branch 101 | 636 | 860 | yes | ok |
| risk | Agent 9143e7f7-8e11-6904-c98e-fb076ea611a1 |  |  |  | refused |
| contact-center | Customer -9222608688654483010 |  |  |  | refused |
| contact-center | Customer -9218325325162838369 |  |  |  | refused |
| contact-center | Customer 4406449607907749601 |  |  |  | refused |
| contact-center | Customer 8322097816940277129 |  |  |  | refused |
| contact-center | Branch 101 |  |  |  | refused |
| contact-center | Agent 9143e7f7-8e11-6904-c98e-fb076ea611a1 | 275 | 600 | yes | ok |

## Isolation

| check | result |
|---|---|
| risk reads memory for a customer others remembered | ok |
| risk's recall of it | ok |
| contact-center's recall of a customer | ok |

## Negative controls: broken reads of memory the oracle must catch

| broken read | caught | by |
|---|---|---|
| reads ignored (risk sees rows its steps never read) | yes | Customer: 1 of 1 rows they can't read, e.g. 4406449607907749601 |
| columns unrestricted (marketing) | yes | Agent: 30 rows of fennmoor-dw.dw_contact_center.dim_agent, which they can't read |
| another's reads (risk read with marketing's steps) | yes | Customer: 1 of 1 rows they can't read, e.g. 4406449607907749601 |
