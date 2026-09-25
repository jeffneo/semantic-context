# M3 score: variables, join confidence, identity

Graph: Neo4j `semanticlayer`. Keys: column concept tags (`concepts.yaml`) and planted findings (`answer_key.json`). Only columns the log actually uses are scored - an unused column has no evidence to place it.

## Variables

- **Identifiers** (675 tagged columns used in the log, scored against id-space concepts): pairwise precision **99.5%**, recall **53.2%**, ARI **0.68**.
- **Identifiers in tables the business consumes** (548 columns): precision **99.5%**, recall **71.4%**, ARI **0.83**. The rest of the gap is raw columns and their staging views that nothing downstream reads (see M2's dead and write-only findings): no join or lineage connects them, so usage gives no evidence either way.
- **Measures, dates, attributes** (699 columns): purity (pairwise precision) **100.0%**. Their concept tags are domains (`money.balance`, `date.day`), coarser than variables by design, so only purity is meaningful: a variable must not straddle two domains, but it may be finer than one.

## Join confidence

Executed joins whose two sides the spec tags as different id spaces: **5**. Flagged suspect: **5**, of which **5** are truly wrong (precision 100%, recall 100%).


All join keys by confidence: {'production': 94, 'single': 50, 'suspect': 5, 'self': 4, 'corroborated': 3}.

## Findings

| finding | result | detail |
|---|---|---|
| F01 One customer, eight id spaces | **pass** | crosswalks recognized: int_customer_identity, online_user, aml party; customer id spaces in or linked to the entity: customer.aml_party_id, customer.cif, customer.ga4_user_id, customer.key, customer.olb_user_id, customer.segment, customer.sf_contact_id |
| F02 The CIF has a dozen spellings | **pass** | 6/7 spellings in the CIF variable; 1 never used in the window, so no evidence either way (legacy_edw.CUST_MSTR.CUST_ID) |
| F03 account_id means three different things | **pass** | deposit / card / Salesforce account_id kept apart: yes (3 variables); the bust_out_candidates join flagged suspect: yes |
| F04 CC means credit card, contact center, or cost center | **partial** | the CC_ID = SITE_CD join flagged suspect: yes; expanding 'CC' per table is M5 (naming) |
| F10 Two teams, two churn models, five column names | **partial** | 3/5 churn columns grouped as competing measures; v3 named sanctioned: yes; unused in the window: legacy_edw.CHURN_MDL_SCR.CHURN_SCR; not linked: sbx_customer_analytics.customer_360_final.churn_risk |
| F12 A column named _usd that holds cents | **pass** | card_spend_usd traced to amount_cents with no /100: yes |
| F13 A join that matches nothing | **pass** | GA4 user_id = cif_number flagged: yes; the online_user bridge named: yes; traced to web_to_branch_journeys: yes |
| F15 Hub keys | **pass** | 3/3 planted hubs flagged (dw_core.dim_date.date_day, dw_core.dim_customer.customer_key, dw_core.dim_account.account_key); 8 hubs in total; recovering subjects around them is M4 |
| F16 A column that went null | **pass** | no finding claims preferred_branch_id broke; the pipeline states that data-level breakage is not determinable from usage |
