# Entitlements, with the warehouse as the oracle

Each test principal through the gateway (`qlsc ask --as`), every gold question and six probes, by both routes (plans/2026-09-27-entitlements.md). **Schema**: no response or LLM prompt names what the principal can't read (the canaries: unreadable tables, hidden columns, their filter values, the log's principals). **Rows**: a SQL answer is the principal's own read of its query; a Cypher answer ran as the principal: every BigQuery job Virtual Graph ran for it is theirs in the warehouse's job log (the pass-through, plans/2026-09-28-jdbc-passthrough.md).

| principal | oracle agrees with the gateway | questions | schema leaks | row incidents | SQL answered | Cypher answered | Cypher refused | routed to Cypher |
|---|---|---|---|---|---|---|---|---|
| marketing | yes | 20 | 0 | 0 | 20 | 4 | 0 | 2 |
| risk | yes | 20 | 0 | 0 | 20 | 6 | 0 | 1 |
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
| marketing | Q02 | sql | ok | no answer: The graph can't answer this. 'High-balance' needs a balance measure (e.g. total_ | none |
| marketing | Q03 | sql | ok | no answer: The graph provided only covers customers, accounts, branches, card transactions  | none |
| marketing | Q04 | cypher | ok | ok | none |
| marketing | Q05 | sql | ok | no answer: Month-end deposit balances come from the fct_daily_account_balances table (ledge | none |
| marketing | Q06 | sql | ok | no answer: None of the labels given (Customer, Account, Branch, CardTransaction, DepositTra | none |
| marketing | Q07 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| marketing | Q08 | sql | ok | no answer: The graph given has no campaign or credit card application data. Its labels cove | none |
| marketing | Q09 | sql | ok | no answer: The graph has no delinquency data. There are no delinquency flags, days-past-due | none |
| marketing | Q10 | sql | ok | no answer: The graph has no data on customer satisfaction (no survey scores, NPS or ratings | none |
| marketing | Q11 | sql | ok | no answer: The graph has no mobile app usage data. There is no login or session table or pr | none |
| marketing | Q12 | sql | ok | no answer: The graph has no contact details for customers: Customer carries only an opaque  | none |
| marketing | Q13 | sql | ok | no answer: The graph only covers tables dim_account, dim_customer, dim_branch, fct_card_tra | none |
| marketing | Q14 | cypher | ok | ok | none |
| marketing | P1 | sql | ok | ok | none |
| marketing | P2 | sql | ok | no answer: The Customer node has a segment property (with 'affluent' as a value), so the af | none |
| marketing | P3 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| marketing | P4 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| marketing | P5 | sql | ok | no answer: The graph cannot answer this. Customer has no cif_number property (only CardTran | none |
| marketing | P6 | sql | ok | ok | none |
| risk | Q01 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| risk | Q02 | sql | ok | no answer: The graph cannot answer this. There is no balance property on Account, Customer  | none |
| risk | Q03 | sql | ok | no answer: The graph provided has no web page visit data (no clickstream or web session tab | none |
| risk | Q04 | cypher | ok | ok | none |
| risk | Q05 | sql | ok | no answer: The graph has no node or property for daily account balances. The bank's own SQL | none |
| risk | Q06 | sql | ok | no answer: This is a data-location question about where SSNs are stored, not a query over r | none |
| risk | Q07 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| risk | Q08 | sql | ok | no answer: The graph given has no credit application or marketing campaign data. The credit | none |
| risk | Q09 | sql | ok | no answer: The graph has no delinquency data. Delinquency lives in `dw_risk.fct_delinquency | none |
| risk | Q10 | sql | no answer | no answer: none of the cohort's tables is in the virtual graph | none |
| risk | Q11 | sql | ok | no answer: The graph has no data on mobile app usage or logins. DepositTransaction.channel  | none |
| risk | Q12 | sql | ok | ok | none |
| risk | Q13 | sql | ok | no answer: The question asks about tables whose names start with 'CC', which is a question  | none |
| risk | Q14 | sql | ok | ok | none |
| risk | P1 | sql | ok | ok | none |
| risk | P2 | sql | ok | ok | none |
| risk | P3 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| risk | P4 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| risk | P5 | sql | ok | no answer: The graph has no deposit balance data. Deposit balances are not a property of Ac | none |
| risk | P6 | sql | ok | ok | none |
| contact-center | Q01 | sql | ok | no answer: The graph can rank contact center sites by account-closure calls (Call.is_accoun | none |
| contact-center | Q02 | sql | ok | no answer: The graph only covers contact-center data (calls, agents, queues, sites). It has | none |
| contact-center | Q03 | sql | ok | no answer: The graph only covers contact-center tables (calls, agents, queues, sites). It h | none |
| contact-center | Q04 | sql | ok | no answer: The graph provided only covers contact-center data (Queue, Call, Agent, ContactC | none |
| contact-center | Q05 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| contact-center | Q06 | sql | ok | no answer: none of the cohort's tables is in the virtual graph | none |
| contact-center | Q07 | sql | ok | no answer: The graph only covers contact-center data (agents, sites, calls, queues). It has | none |
| contact-center | Q08 | sql | ok | no answer: The graph provided only covers contact center data (Call, Agent, Queue, ContactC | none |
| contact-center | Q09 | sql | ok | no answer: The graph provided only covers contact center data (calls, agents, queues, conta | none |
| contact-center | Q10 | sql | ok | no answer: The graph has agent tenure (Agent.tenure_months) but no customer satisfaction da | none |
| contact-center | Q11 | sql | ok | no answer: The graph given only covers contact center data (calls, agents, queues, sites).  | none |
| contact-center | Q12 | sql | ok | no answer: The graph given covers only contact-center data (Call, Agent, ContactCenterSite, | none |
| contact-center | Q13 | sql | ok | no answer: The question asks about the contents of tables whose names start with 'CC', whic | none |
| contact-center | Q14 | sql | ok | no answer: The graph only covers the contact center (calls, agents, queues, sites). It has  | none |
| contact-center | P1 | sql | ok | no answer: The graph has no customer entity and no customer address or state property. The  | none |
| contact-center | P2 | sql | ok | no answer: The graph given only covers contact-center data (agents, calls, queues, sites).  | none |
| contact-center | P3 | sql | ok | no answer: The graph only covers contact-center data (agents, sites, calls, queues). It has | none |
| contact-center | P4 | sql | ok | ok | none |
| contact-center | P5 | sql | ok | no answer: The graph given only covers contact-center data (calls, agents, queues, sites).  | none |
| contact-center | P6 | sql | ok | no answer: The graph provided covers only contact-center data (calls, queues, agents, sites | none |
