# Navigation: question -> tables (qlsc ask)

The 14 gold questions, embedded and walked down the semantic layer to a cohort of 8 tables. **reached** = expected tables anywhere under the opened level-1 groups (what the choice of groups allows); **recall** = expected tables in the final 8; **hit** = questions with an expected or acceptable table in the 8; **traps** = avoid-tables in the 8.

| groups | ranking | reached | recall | hit | traps |
|---|---|---|---|---|---|
| traversal | usage | 68% | 62% | 13/14 | 4 |
| traversal | round_robin | 68% | 56% | 13/14 | 6 |
| flat | usage | 68% | 62% | 13/14 | 4 |
| flat | round_robin | 68% | 53% | 13/14 | 6 |
| combined | usage | 68% | 62% | 13/14 | 4 |
| combined | round_robin | 68% | 53% | 13/14 | 6 |

## Per question (traversal/usage)

| Q | reached | recall | missed | traps |
|---|---|---|---|---|
| Q01 | 100% | 100% |  |  |
| Q02 | 0% | 0% | dw_customer.customer_360 | sbx_customer_analytics.customer_360_final |
| Q03 | 100% | 100% |  | analytics_312874659.events_* |
| Q04 | 50% | 50% | dw_core.dim_customer |  |
| Q05 | 50% | 50% | dw_core.fct_daily_account_balances | legacy_edw.ACCT_DLY_BAL, legacy_edw.EOM_BAL_SNAP |
| Q06 | 40% | 20% | legacy_edw.CUST_MSTR, legacy_edw.CUST_MSTR_BKP_20250211, sbx_risk.kyc_review_extract, core_banking_cdc.CUSTOMER |  |
| Q07 | 100% | 100% |  |  |
| Q08 | 100% | 100% |  |  |
| Q09 | 67% | 33% | dw_core.dim_branch, dw_risk.fct_delinquency_daily |  |
| Q10 | 100% | 100% |  |  |
| Q11 | 100% | 100% |  |  |
| Q12 | 0% | 0% | dw_customer.customer_360 |  |
| Q13 | 50% | 17% | legacy_edw.CC_ACCT_MSTR, legacy_edw.CC_AGENT_DLY, legacy_edw.CC_CALL_VOL_DLY, legacy_edw.CC_EXPNS_MTHLY, legacy_edw.CC_TXN_HIST |  |
| Q14 | 100% | 100% |  |  |
