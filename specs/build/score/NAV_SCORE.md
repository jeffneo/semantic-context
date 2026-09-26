# Navigation: question -> tables (pipeline/navigate.py)

The 14 gold questions, embedded and walked down the semantic layer to a cohort of 8 tables. **reached** = expected tables anywhere under the opened level-1 groups (what the choice of groups allows); **recall** = expected tables in the final 8; **hit** = questions with an expected or acceptable table in the 8; **traps** = avoid-tables in the 8.

| groups | ranking | reached | recall | hit | traps |
|---|---|---|---|---|---|
| traversal | usage | 71% | 59% | 13/14 | 1 |
| traversal | round_robin | 71% | 61% | 12/14 | 3 |
| flat | usage | 78% | 59% | 13/14 | 1 |
| flat | round_robin | 78% | 65% | 13/14 | 3 |
| combined | usage | 78% | 59% | 13/14 | 1 |
| combined | round_robin | 78% | 65% | 13/14 | 3 |

## Per question (flat/round_robin)

| Q | reached | recall | missed | traps |
|---|---|---|---|---|
| Q01 | 100% | 67% | dw_contact_center.fct_contacts_all | sbx_finance.cc_cost_per_call_fy25 |
| Q02 | 0% | 0% | dw_customer.customer_360 |  |
| Q03 | 100% | 50% | dw_digital.fct_web_sessions | analytics_312874659.events_* |
| Q04 | 100% | 100% |  |  |
| Q05 | 100% | 100% |  | legacy_edw.EOM_BAL_SNAP |
| Q06 | 40% | 20% | legacy_edw.CUST_MSTR, legacy_edw.CUST_MSTR_BKP_20250211, sbx_risk.kyc_review_extract, core_banking_cdc.CUSTOMER |  |
| Q07 | 100% | 100% |  |  |
| Q08 | 100% | 50% | dw_marketing.fct_campaign_attribution |  |
| Q09 | 100% | 67% | dw_core.dim_branch |  |
| Q10 | 100% | 100% |  |  |
| Q11 | 100% | 100% |  |  |
| Q12 | 0% | 0% | dw_customer.customer_360 |  |
| Q13 | 50% | 50% | legacy_edw.CC_ACCT_MSTR, legacy_edw.CC_AGENT_DLY, legacy_edw.CC_TXN_HIST |  |
| Q14 | 100% | 100% |  |  |
