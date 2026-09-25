# M6 score: answering the 14 questions

Agent model: `claude-haiku-4-5-20251001`; must-handle judge: `claude-sonnet-5`. **Semantic** = the tools over this graph (pipeline/tools.py); **catalog only** = the same model, prompt skeleton and loop with only BigQuery's catalog (names, columns, types, partitioning, dry runs). Each mode was run 3 times independently; cells show the mean (min-max).

| | semantic layer | catalog only |
|---|---|---|
| questions fully right: every expected table, no trap, no wrong join, SQL valid | **12.7/14 (12-13)** | 9.3/14 (9-10) |
| expected-table recall | 95% (90%-98%) | 79% (76%-82%) |
| trap tables used (the key lists 26) | **0** | 1 |
| joins between different id spaces | 0 | 0.3 (0-1) |
| SQL that dry-runs clean | 12/12 | 12/12 |
| must-handle items (judged; pass 1, partial 0.5) | **69% (62%-81%)** | 26% (16%-32%) |
| tool calls per run | 145.3 (135-158) | 139 (127-145) |

Agent LLM cost of the uncached calls this scoring made: semantic $3.42, catalog only $1.87 (at $1/$5 per million input/output tokens).

**F18** (negative control: the BPO double count needs domain knowledge): **pass**. No finding claims it (0); the `limits` finding says ledger double counts are not determinable from usage (stated); Q01 answers adding `gl_erp.vendor_invoice`: 0 of 3.

## Semantic layer: per question, over 3 runs

| Q | fully right | table recall | tables missed (runs) | traps used (runs) | wrong joins | must-handle | calls |
|---|---|---|---|---|---|---|---|
| Q01 | 0/3 | 44% | dw_contact_center.fct_contacts_all (3), dw_contact_center.dim_cc_site (1), dw_contact_center.fct_cc_site_cost_monthly (1) |  | 0 | 4% | 15 |
| Q02 | 3/3 | 100% |  |  | 0 | 67% | 14 |
| Q03 | 3/3 | 100% |  |  | 0 | 8% | 14 |
| Q04 | 3/3 | 100% |  |  | 0 | 83% | 12 |
| Q05 | 3/3 | 100% |  |  | 0 | 67% | 9 |
| Q06 | 2/3 | 87% | sbx_risk.kyc_review_extract (1), aml_kyc.party (1) |  | 0 | 75% | 1 |
| Q07 | 3/3 | 100% |  |  | 0 | 100% | 8 |
| Q08 | 3/3 | 100% |  |  | 0 | 100% | 14 |
| Q09 | 3/3 | 100% |  |  | 0 | 100% | 12 |
| Q10 | 3/3 | 100% |  |  | 0 | 83% | 10 |
| Q11 | 3/3 | 100% |  |  | 0 | 100% | 5 |
| Q12 | 3/3 | 100% |  |  | 0 | 50% | 12 |
| Q13 | 3/3 | 100% |  |  | 0 | 100% | 8 |
| Q14 | 3/3 | 100% |  |  | 0 | 33% | 11 |

Must-handle items not passed, with the judge's reason (first run where it happened):

- Q01 [fail/fail/fail] "Last year" (2025) spans the Avaya -> Genesys cutover on 2025-10-01: volume needs both (fct_contacts - The answer relies solely on a pre-built reporting table (rpt_site_cost_per_contact) which is stated to derive closure_calls from is_account_closure_call flag in fct_calls (Genesys-based). There is no evidence or discussion that th
- Q01 [partial/fail/fail] Site cost is GL expense on each site's cost center, including the BPO site's AP lines. - The answer states total_expense includes payroll, vendor, and other expenses by cost center/site, which gestures at GL expense inclusion, but does not explicitly mention BPO site AP lines or confirm the pre-built table handles thi
- Q01 [fail/fail/fail] Closure calls before 2026-06-02 are not coded ACCT_CLOSE (F17) - irrelevant for 2025 Genesys, but Av - The warnings mention the ACCT_CLOSE wrapup code drift on 2026-06-03 and note it's not directly relevant for 2025 data, but this reasoning is flawed since it implies Genesys closure calls in 2025 are correctly captured, when in fac
- Q01 [fail/fail/fail] Attribute contacts to the agent's site, not the queue's (overflow routing). - The answer does not mention agent-site vs queue-site attribution at all, either in SQL or in warnings/cannot_tell. It relies on the pre-built table without verifying or stating how site attribution is handled for overflow routing.
- Q02 [pass/partial/partial] Use the latest score_date, not all history. - The answer relies on customer_360.churn_probability, and claims (in the joins section) that this field 'comes from ml_scores.churn_score_v3 on customer_key, using most recent score_date.' However, the actual SQL does not explicitl
- Q03 [fail/fail/fail] GA4 identities resolve to customers only via online_user.ga4_user_id. - The answer joins fct_web_sessions directly to dim_customer via customer_key, with no mention of online_user or ga4_user_id as the resolution path from GA4 identities to customers.
- Q03 [fail/fail/partial] Only logged-in sessions can be attributed; say what fraction that is. - The answer does not mention that only logged-in sessions can be attributed to customers, nor does it quantify what fraction of sessions/traffic this represents.
- Q04 [pass/pass/fail] Purchases only (is_purchase), not payments/refunds. - The SQL does not filter on is_purchase or any equivalent condition to exclude payments/refunds, and no warning or caveat addresses this omission.
- Q05 [pass/partial/partial] Month-end = last balance_date of each month per account. - The SQL only covers a single month (June 2026) rather than computing month-end balances per account for each month generally. Within that month, it correctly picks the last balance_date per account via ARRAY_AGG ordered by balance
- Q06 [partial/partial/pass] Separate raw (5 tables) from hashed. - The answer lists only 3 raw tables (CUST_MSTR, CUST_MSTR_BKP_20250211, core_banking_cdc.CUSTOMER) plus stg_los__applicant with ssn_last4 (4 total, and ssn_last4 is partial SSN not full raw SSN), against 4 hashed tables. This does 
- Q06 [pass/partial/pass] Flag the three raw copies outside restricted datasets (F08). - The answer does flag raw copies outside restricted zones (CUST_MSTR, CUST_MSTR_BKP_20250211, kyc_review_extract as 'avoid'/outside restricted), and notes aml_kyc.party is in a restricted dataset. However, core_banking_cdc.CUSTOMER
- Q10 [pass/partial/pass] BPO agents have no hire date (not Fennmoor employees). - The answer notes that survey responses may lack tenure data due to unmatched agent_user_id, grouping these as 'Unknown', and mentions 'unmatched or inactive agents' - but never explicitly states that BPO agents (as opposed to Fenn
- Q12 [pass/partial/fail] Respect email_opt_in (dim_customer). - The answer filters on email_opt_in = TRUE, satisfying the intent of respecting opt-in status, but sources it from int_customer_contact_points rather than dim_customer as specified in the answer key. The join is a LEFT JOIN yet fil
- Q14 [partial/partial/fail] Card and deposit close-reason codes differ (CH vs CUST_REQ) - map them. - The answer notes that close reason values come from different source systems and mentions codes like CUST_REQ and CH in the context of is_voluntary logic, indicating awareness that codes differ. However, it does not actually map C

## Catalog only: per question, over 3 runs

| Q | fully right | table recall | tables missed (runs) | traps used (runs) | wrong joins | must-handle | calls |
|---|---|---|---|---|---|---|---|
| Q01 | 0/3 | 67% | dw_contact_center.fct_contacts_all (3) |  | 0 | 0% | 17 |
| Q02 | 3/3 | 100% |  |  | 0 | 17% | 10 |
| Q03 | 1/3 | 67% | dw_digital.fct_web_sessions (2) |  | 1 | 8% | 17 |
| Q04 | 3/3 | 100% |  |  | 0 | 100% | 10 |
| Q05 | 3/3 | 100% |  |  | 0 | 17% | 9 |
| Q06 | 0/3 | 20% | legacy_edw.CUST_MSTR_BKP_20250211 (3), sbx_risk.kyc_review_extract (3), aml_kyc.party (3), core_banking_cdc.CUSTOMER (3) |  | 0 | 0% | 7 |
| Q07 | 3/3 | 100% |  |  | 0 | 0% | 7 |
| Q08 | 3/3 | 100% |  |  | 0 | 83% | 12 |
| Q09 | 0/3 | 56% | dw_core.dim_account (3), dw_risk.fct_delinquency_daily (1) |  | 0 | 0% | 11 |
| Q10 | 3/3 | 100% |  |  | 0 | 0% | 7 |
| Q11 | 3/3 | 100% |  |  | 0 | 67% | 6 |
| Q12 | 0/3 | 0% | dw_customer.customer_360 (3) | sbx_marketing.email_list_affluent_apr26 (3) | 0 | 50% | 7 |
| Q13 | 3/3 | 100% |  |  | 0 | 17% | 10 |
| Q14 | 3/3 | 100% |  |  | 0 | 0% | 10 |

Must-handle items not passed, with the judge's reason (first run where it happened):

- Q01 [fail/fail/fail] "Last year" (2025) spans the Avaya -> Genesys cutover on 2025-10-01: volume needs both (fct_contacts - The answer uses a pre-aggregated table agg_site_monthly with a 'closure_calls' field, not fct_contacts_all, and does not mention or handle the Avaya->Genesys cutover or combining both systems' data sources.
- Q01 [fail/fail/fail] Site cost is GL expense on each site's cost center, including the BPO site's AP lines. - The answer uses a pre-built fct_cc_site_cost_monthly table (payroll/vendor/other) rather than deriving from GL expense on cost centers, and does not mention BPO AP lines or cost center linkage at all.
- Q01 [fail/fail/fail] Closure calls before 2026-06-02 are not coded ACCT_CLOSE (F17) - irrelevant for 2025 Genesys, but Av - The answer relies on a generic 'closure_calls' field from an aggregate table without any discussion of disposition codes (ACCT_CLOSE, CLSACCT/CLOSE) or the coding caveat; this nuance is entirely unaddressed.
- Q01 [fail/fail/fail] Attribute contacts to the agent's site, not the queue's (overflow routing). - The answer uses agg_site_monthly.site_id directly without discussing agent-vs-queue attribution or overflow routing at all.
- Q02 [fail/partial/fail] Use the latest score_date, not all history. - The customer_360 table is treated as if it has no date column, and the answer explicitly states it cannot verify data currency rather than filtering to the latest score_date. No filtering on score_date is applied in the SQL.
- Q03 [fail/fail/fail] GA4 identities resolve to customers only via online_user.ga4_user_id. - The answer joins GA4 events directly to fct_digital_logins via ga4.user_id = logins.olb_user_id, rather than resolving identity through online_user.ga4_user_id as specified. No mention of online_user table at all.
- Q03 [partial/fail/fail] Only logged-in sessions can be attributed; say what fraction that is. - The answer acknowledges in warnings that only authenticated/logged-in sessions can be linked and anonymous visitors are excluded, but it never quantifies or states what fraction of sessions are logged-in vs total.
- Q05 [fail/fail/partial] Month-end = last balance_date of each month per account. - The query filters using balance_date = LAST_DAY(balance_date, MONTH), i.e., the literal calendar month-end date, rather than computing the last available balance_date per account within each month. If an account's last balance rec
- Q06 [fail/fail/fail] Separate raw (5 tables) from hashed. - The answer identifies only 1 raw table (CUST_MSTR) and 1 hashed table (consumer_attributes_monthly), plus 1 partial (last 4 digits). The answer key expects 5 raw tables to be identified, but only 1 is found, missing 4 raw copies.
- Q06 [fail/fail/fail] Flag the three raw copies outside restricted datasets (F08). - The answer does not mention dataset restriction levels (F08) at all, nor does it identify three raw copies outside restricted datasets. Only one raw table is flagged as a general security concern, with no reference to restricted d
- Q07 [fail/fail/fail] Alerts without a case are not confirmed. - The answer relies solely on the is_confirmed_fraud boolean field from fct_fraud_alerts and does not reference any case table or join to verify that confirmed alerts have an associated case. There's no mention or handling of alerts
- Q08 [pass/pass/partial] Conversion behavior identifies card applications. - The answer does not filter or check the conversion_behavior field in fct_campaign_attribution to confirm it specifically denotes credit card application conversions. Instead it joins fct_campaign_attribution to fct_credit_applicat
- Q09 [fail/fail/fail] Denominator is open loans, from dim_account, not only delinquent ones. - The answer uses fct_delinquency_daily as the source for total_loans (all loans present in that fact table on the latest snapshot), not dim_account filtered to open loans. It does not join to dim_account or filter for open loan sta
- Q10 [fail/fail/fail] BPO agents have no hire date (not Fennmoor employees). - The answer's SQL filters out records where tenure_months IS NULL, which would exclude BPO agents without a hire date, but the answer never explicitly states or acknowledges this caveat about BPO agents lacking hire dates. It only 
- Q11 [fail/pass/pass] Count customers (cif_number), not olb_user_ids - joint users have several. - The SQL uses COUNT(DISTINCT olb_user_id) instead of cif_number, which is exactly what the requirement warns against. Although the answer acknowledges this discrepancy in warnings and cannot_tell sections, it does not correct the S
- Q12 [fail/pass/partial] Respect email_opt_in (dim_customer). - The SQL does not filter or join on email_opt_in from dim_customer; it only checks primary_email IS NOT NULL. The answer merely flags in warnings/cannot_tell that opt-in status is unknown and should be checked before sending, but d
- Q13 [fail/fail/partial] Three different meanings of CC, each named correctly (F04). - The answer only identifies one meaning of CC ('Contact Center') across all 9 tables, treating them all as contact center related. It does not recognize that CC_ACCT_MSTR and CC_TXN_HIST likely refer to 'Credit Card' (given credit 
- Q14 [fail/fail/fail] Card and deposit close-reason codes differ (CH vs CUST_REQ) - map them. - The answer groups raw close_reason values without mapping CH (card) and CUST_REQ (deposit) codes to a common meaning; it does not acknowledge or reconcile that the two product types use different coding schemes for closure reasons

