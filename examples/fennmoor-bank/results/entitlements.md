# Entitlements, with the warehouse as the oracle

Each test principal through the gateway (`qlsc ask --as`), every gold question and six probes, by both routes (plans/2026-09-27-entitlements.md). **Schema**: no response or LLM prompt names what the principal can't read (the canaries: unreadable tables, hidden columns, their filter values, the log's principals). **Rows**: a SQL answer is the principal's own read of its query; a Cypher answer ran as the principal: every BigQuery job Virtual Graph ran for it is theirs in the warehouse's job log (the pass-through, plans/2026-09-28-jdbc-passthrough.md).

| principal | oracle agrees with the gateway | questions | schema leaks | row incidents | SQL answered | Cypher answered | Cypher refused | routed to Cypher |
|---|---|---|---|---|---|---|---|---|
| marketing | yes | 20 | 0 | 0 | 20 | 4 | 0 | 2 |
| risk | yes | 20 | 0 | 0 | 20 | 7 | 0 | 2 |
| contact-center | yes | 20 | 0 | 0 | 20 | 1 | 0 | 0 |

## The pass-through, reached directly

| query | refused |
|---|---|
| no token (a Neo4j user reaching the virtual graph directly) | yes |
| a forged token (marketing's name, risk's signature) | yes |
| an expired token | yes |

## Negative controls: broken gateways the checks must catch

| broken gateway | principal | caught | by |
|---|---|---|---|
| navigation unfiltered (the trace shows everything; queries still run as the principal) | marketing | yes | schema |
| navigation unfiltered (the trace shows everything; queries still run as the principal) | contact-center | yes | schema |
| hidden columns and their filter values shown | marketing | yes | schema |
| SQL run as the estate, not the principal | risk | yes | rows |
| the gateway signs as the data source, not the principal | risk | yes | rows |

## Per question

| principal | question | routed | SQL | Cypher | leaks |
|---|---|---|---|---|---|
| marketing | Q01 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| marketing | Q02 | sql | ok | no answer: The graph can't answer this. It has no customer balance property (total_deposit_ | none |
| marketing | Q03 | sql | ok | no answer: The graph given has no web page visit or call center data. It only covers custom | none |
| marketing | Q04 | cypher | ok | ok | none |
| marketing | Q05 | sql | ok | no answer: Month-end deposit balances come from the daily account balances table (fct_daily | none |
| marketing | Q06 | sql | ok | no answer: The graph has no property holding a Social Security number, raw or hashed, on an | none |
| marketing | Q07 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| marketing | Q08 | sql | ok | no answer: The graph provided has no campaign or attribution data and no credit card applic | none |
| marketing | Q09 | sql | ok | no answer: The graph has no delinquency data. Account has only a generic status_code and no | none |
| marketing | Q10 | sql | ok | no answer: The graph has no agent or employee entity with a tenure measure, and no customer | none |
| marketing | Q11 | sql | ok | no answer: The graph has no mobile app usage or login/session data. DepositTransaction.chan | none |
| marketing | Q12 | sql | ok | no answer: The Customer node has segment, email_opt_in, sf_contact_id and other flags, but  | none |
| marketing | Q13 | sql | ok | no answer: The graph has no table or label whose name starts with CC. Its tables are dim_ac | none |
| marketing | Q14 | cypher | ok | ok | none |
| marketing | P1 | sql | ok | ok | none |
| marketing | P2 | sql | ok | no answer: The Customer node has a segment property (with an 'affluent' value), but it has  | none |
| marketing | P3 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| marketing | P4 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| marketing | P5 | sql | ok | no answer: The graph cannot answer this. Deposit balances live in a customer_360 table (tot | none |
| marketing | P6 | sql | ok | ok | none |
| risk | Q01 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| risk | Q02 | sql | ok | no answer: The graph has no churn-risk measure and no balance data. Customer and Account no | none |
| risk | Q03 | sql | ok | no answer: The graph provided has no web page visit or web session data and no call or cont | none |
| risk | Q04 | cypher | ok | ok | none |
| risk | Q05 | sql | ok | no answer: Month-end deposit balances live in fct_daily_account_balances (ledger_balance by | none |
| risk | Q06 | cypher | ok | ok | none |
| risk | Q07 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| risk | Q08 | sql | ok | no answer: The graph given has no credit card application or marketing campaign data. The l | none |
| risk | Q09 | sql | ok | no answer: The graph has no delinquency data. Delinquency status (days past due, e.g. DPD > | none |
| risk | Q10 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| risk | Q11 | sql | ok | no answer: The graph has no mobile app usage or login/session data. DepositTransaction.chan | none |
| risk | Q12 | sql | ok | ok | none |
| risk | Q13 | sql | ok | no answer: The graph only exposes these tables: dim_customer, dim_account, dim_branch, fct_ | none |
| risk | Q14 | sql | ok | ok | none |
| risk | P1 | sql | ok | ok | none |
| risk | P2 | sql | ok | ok | none |
| risk | P3 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| risk | P4 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| risk | P5 | sql | ok | no answer: The graph has no deposit balance data. Account has no balance property, and Depo | none |
| risk | P6 | sql | ok | ok | none |
| contact-center | Q01 | sql | ok | no answer: Cancellation counts per contact center can be computed from Call.is_account_clos | none |
| contact-center | Q02 | sql | ok | no answer: The graph provided only covers contact center data (calls, agents, queues, sites | none |
| contact-center | Q03 | sql | ok | no answer: The graph only covers contact-center data (calls, agents, queues, sites). It has | none |
| contact-center | Q04 | sql | ok | no answer: The graph given only covers contact center data (Call, Queue, Agent, ContactCent | none |
| contact-center | Q05 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| contact-center | Q06 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| contact-center | Q07 | sql | ok | no answer: The graph given only covers contact center data (Agent, ContactCenterSite, Call, | none |
| contact-center | Q08 | sql | ok | no answer: The graph provided only covers contact center data: ContactCenterSite, Call, Age | none |
| contact-center | Q09 | sql | ok | no answer: The graph provided only covers contact center data (ContactCenterSite, Call, Age | none |
| contact-center | Q10 | sql | ok | no answer: The graph has no customer satisfaction data. Satisfaction scores (nps_score, is_ | none |
| contact-center | Q11 | sql | ok | no answer: The graph only covers contact-center data: calls (voice media type), agents, que | none |
| contact-center | Q12 | sql | ok | no answer: The graph given covers only contact-center data (calls, agents, queues, sites).  | none |
| contact-center | Q13 | sql | ok | no answer: The question asks about the contents of tables whose names start with CC, which  | none |
| contact-center | Q14 | sql | ok | no answer: The graph only covers contact-center data (calls, agents, queues, sites). It has | none |
| contact-center | P1 | sql | ok | no answer: The graph has no customer entity and no customer state. The only state property  | none |
| contact-center | P2 | sql | ok | no answer: The graph provided only covers contact-center data (Agent, Call, ContactCenterSi | none |
| contact-center | P3 | sql | ok | no answer: The graph only covers contact center data (agents, calls, queues, sites). It has | none |
| contact-center | P4 | sql | ok | ok | none |
| contact-center | P5 | sql | ok | no answer: The graph provided only covers contact center data (calls, agents, queues, sites | none |
| contact-center | P6 | sql | ok | no answer: The graph provided only covers contact center data (calls, queues, agents, sites | none |
