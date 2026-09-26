# Reference answers

Each gold question's hand-written reference query (`eval/reference/`), run against the filled estate. These are the answers execution accuracy scores against.

## Q01. Which contact centers see the most account cancellations, and what did each cost to run last year?

| site_name | closure_contacts | contacts | expense_2025 |
|---|---|---|---|
| Tulsa Contact Center | 3,564 | 51,737 | 71876887.16 |
| Spokane Contact Center | 1,861 | 26,214 | 71486853.56 |
| Manila BPO | 1,532 | 21,049 | 70736205.57 |

3 rows; 0 MiB billed.

## Q02. What is the churn risk of our high-balance customers?

| segment | customers | avg_churn_probability | high_risk |
|---|---|---|---|
| mass | 526 | 0.352 | 46 |
| mass_affluent | 183 | 0.344 | 17 |
| affluent | 71 | 0.338 | 5 |
| small_business | 41 | 0.354 | 3 |
| private | 14 | 0.38 | 1 |

5 rows; 10 MiB billed.

## Q03. Which web pages do customers visit before they call us?

| landing_page | sessions_before_a_call | logged_in_share |
|---|---|---|
| https://www.fennmoor.example/ | 866 | 0.852 |
| https://www.fennmoor.example/login | 611 | 0.852 |
| https://www.fennmoor.example/accounts | 574 | 0.852 |
| https://www.fennmoor.example/credit-cards | 263 | 0.852 |
| https://www.fennmoor.example/checking | 257 | 0.852 |
| https://www.fennmoor.example/help | 229 | 0.852 |
| https://www.fennmoor.example/savings | 227 | 0.852 |
| https://www.fennmoor.example/branch-locator | 217 | 0.852 |
| https://www.fennmoor.example/contact | 190 | 0.852 |
| https://www.fennmoor.example/credit-cards/apply | 162 | 0.852 |
| https://www.fennmoor.example/loans/heloc | 149 | 0.852 |
| https://www.fennmoor.example/help/lost-card | 145 | 0.852 |
| https://www.fennmoor.example/rates | 117 | 0.852 |
| https://www.fennmoor.example/help/dispute-a-charge | 116 | 0.852 |
| https://www.fennmoor.example/help/close-account | 96 | 0.852 |

15 rows; 0 MiB billed.

## Q04. Card spend by merchant category and customer segment, last quarter.

| segment | mcc_category_group | spend | purchases |
|---|---|---|---|
| affluent | DINING | 2184203.3 | 32,490 |
| affluent | RETAIL | 2162290.3 | 32,326 |
| affluent | GROCERY | 1859425.34 | 27,822 |
| affluent | FUEL | 1107181.31 | 16,493 |
| affluent | TRAVEL | 884251.86 | 13,291 |
| affluent | UTILITIES | 658056.68 | 9,698 |
| affluent | MONEY_TRANSFER | 268359.69 | 4,068 |
| affluent | CRYPTO | 157533.86 | 2,439 |
| affluent | GAMBLING | 149247.51 | 2,229 |
| mass | RETAIL | 14967771.83 | 223,430 |
| mass | DINING | 14861978.49 | 222,738 |
| mass | GROCERY | 12789898.39 | 191,367 |
| mass | FUEL | 7663581.23 | 114,187 |
| mass | TRAVEL | 6099151.94 | 90,742 |
| mass | UTILITIES | 4499745.78 | 66,998 |
| mass | MONEY_TRANSFER | 1861510.3 | 27,874 |
| mass | CRYPTO | 1125493.26 | 17,145 |
| mass | GAMBLING | 1002002.78 | 15,216 |
| mass_affluent | DINING | 5746097.89 | 85,066 |
| mass_affluent | RETAIL | 5708872.86 | 84,904 |
| mass_affluent | GROCERY | 4883413.5 | 72,838 |
| mass_affluent | FUEL | 2907275.26 | 43,212 |
| mass_affluent | TRAVEL | 2293912.48 | 34,668 |
| mass_affluent | UTILITIES | 1701514.91 | 25,331 |
| mass_affluent | MONEY_TRANSFER | 708577.98 | 10,606 |
| mass_affluent | CRYPTO | 445288.18 | 6,622 |
| mass_affluent | GAMBLING | 392206.22 | 5,822 |
| private | RETAIL | 474039.56 | 7,152 |
| private | DINING | 470476.82 | 7,144 |
| private | GROCERY | 405713.73 | 6,112 |
| private | FUEL | 246999.13 | 3,746 |
| private | TRAVEL | 198459.25 | 2,897 |
| private | UTILITIES | 140752.6 | 2,101 |
| private | MONEY_TRANSFER | 62194.4 | 919 |
| private | GAMBLING | 31736.73 | 503 |
| private | CRYPTO | 31579.79 | 530 |
| small_business | DINING | 1230012.17 | 18,428 |
| small_business | RETAIL | 1193433.47 | 18,095 |
| small_business | GROCERY | 1040489.66 | 15,700 |
| small_business | FUEL | 617484.26 | 9,420 |
| small_business | TRAVEL | 525075.47 | 7,485 |
| small_business | UTILITIES | 370861.99 | 5,483 |
| small_business | MONEY_TRANSFER | 156284.11 | 2,350 |
| small_business | CRYPTO | 92901.47 | 1,394 |
| small_business | GAMBLING | 75715.45 | 1,219 |

45 rows; 74 MiB billed.

## Q05. Month-end deposit balances by product line.

| month | product_line | month_end_balance |
|---|---|---|
| 2026-04-01 | CD | 15519768.25 |
| 2026-04-01 | CHK | 119144471.87 |
| 2026-04-01 | MMA | 14089313.55 |
| 2026-04-01 | SAV | 84386926.11 |
| 2026-05-01 | CD | 17632338.9 |
| 2026-05-01 | CHK | 124005862.73 |
| 2026-05-01 | MMA | 13379598.95 |
| 2026-05-01 | SAV | 85145442.72 |
| 2026-06-01 | CD | 17441556.83 |
| 2026-06-01 | CHK | 118053191.18 |
| 2026-06-01 | MMA | 12535117.54 |
| 2026-06-01 | SAV | 85191180.33 |

12 rows; 122 MiB billed.

## Q06. Where do we store Social Security numbers, raw or hashed?

| column_ | form | values_ |
|---|---|---|
| aml_kyc.party.tax_id | raw | 24,300 |
| core_banking_cdc.CUSTOMER.TAX_ID | raw | 24,300 |
| legacy_edw.CUST_MSTR.SSN_NBR | raw | 24,300 |
| legacy_edw.CUST_MSTR_BKP_20250211.SSN_NBR | raw | 24,300 |
| sbx_risk.kyc_review_extract.tax_id | raw | 24,300 |
| credit_bureau.consumer_attributes_monthly.SSN_HASH | hashed | 607,500 |
| dw_compliance.dim_aml_party.tax_id_hash | hashed | 24,300 |
| dw_core.dim_customer.tax_id_hash | hashed | 24,300 |

8 rows; 0 MiB billed.

## Q07. What share of fraud alerts are confirmed fraud, by channel?

| channel | alerts | confirmed | confirmed_share |
|---|---|---|---|
| CNP | 77,442 | 7,750 | 0.1001 |
| ONLINE | 57,477 | 5,702 | 0.0992 |
| MOBILE | 52,098 | 5,174 | 0.0993 |
| CP | 31,198 | 3,022 | 0.0969 |
| ATM | 15,652 | 1,578 | 0.1008 |
| BRANCH | 13,072 | 1,327 | 0.1015 |
| P2P | 13,061 | 1,288 | 0.0986 |

7 rows; 0 MiB billed.

## Q08. Which marketing campaigns drove credit card applications?

| campaign_name | card_applications |
|---|---|
| HELOC Rate Drop | 15,098 |
| Card Activation Reminder | 13,932 |
| Checking Bonus 300 | 13,272 |
| Digital Enrollment Nudge | 13,089 |
| Travel Rewards Launch | 12,860 |
| Spring Cash Back | 12,829 |
| Savings Rate Alert | 12,471 |

7 rows; 0 MiB billed.

## Q09. Loan delinquency rate by product and branch.

| product_code | branch_name | open_loans | delinquent | delinquency_rate |
|---|---|---|---|---|
| MTG-30F | Fennmoor Boise Branch | 229 | 14 | 0.0611 |
| MTG-30F | Fennmoor Topeka Branch | 213 | 10 | 0.0469 |
| HELOC-STD | Fennmoor Boise Branch | 200 | 12 | 0.06 |
| HELOC-STD | Fennmoor Tulsa Branch | 199 | 19 | 0.0955 |
| MTG-30F | Fennmoor Tulsa Branch | 194 | 11 | 0.0567 |
| HELOC-STD | Fennmoor Kansas City Branch | 190 | 7 | 0.0368 |
| HELOC-STD | Fennmoor Topeka Branch | 188 | 10 | 0.0532 |
| MTG-30F | Fennmoor Kansas City Branch | 174 | 9 | 0.0517 |
| HELOC-STD | Fennmoor Wichita Branch | 152 | 7 | 0.0461 |
| HELOC-STD | Fennmoor Bartlesville Branch | 149 | 16 | 0.1074 |
| MTG-30F | Fennmoor Wichita Branch | 149 | 8 | 0.0537 |
| MTG-30F | Fennmoor Stillwater Branch | 147 | 8 | 0.0544 |
| HELOC-STD | Fennmoor Stillwater Branch | 141 | 9 | 0.0638 |
| MTG-30F | Fennmoor Oklahoma City Branch | 137 | 5 | 0.0365 |
| HELOC-STD | Fennmoor Oklahoma City Branch | 129 | 9 | 0.0698 |
| MTG-30F | Fennmoor Bartlesville Branch | 124 | 9 | 0.0726 |
| AUTO-STD | Fennmoor Topeka Branch | 122 | 12 | 0.0984 |
| HELOC-STD | Fennmoor Norman Branch | 117 | 6 | 0.0513 |
| MTG-30F | Fennmoor Norman Branch | 115 | 4 | 0.0348 |
| HELOC-STD | Fennmoor Omaha Branch | 112 | 12 | 0.1071 |
| PL-STD | Fennmoor Kansas City Branch | 103 | 9 | 0.0874 |
| HELOC-STD | Fennmoor Springfield Branch | 103 | 14 | 0.1359 |
| AUTO-STD | Fennmoor Tulsa Branch | 102 | 2 | 0.0196 |
| PL-STD | Fennmoor Topeka Branch | 99 | 6 | 0.0606 |
| PL-STD | Fennmoor Boise Branch | 97 | 7 | 0.0722 |
| MTG-30F | Fennmoor Springfield Branch | 97 | 7 | 0.0722 |
| MTG-30F | Fennmoor Omaha Branch | 94 | 5 | 0.0532 |
| PL-STD | Fennmoor Tulsa Branch | 91 | 7 | 0.0769 |
| AUTO-STD | Fennmoor Boise Branch | 91 | 2 | 0.022 |
| MTG-30F | Fennmoor Lincoln Branch | 87 | 3 | 0.0345 |
| HELOC-STD | Fennmoor Lincoln Branch | 84 | 3 | 0.0357 |
| MTG-30F | Fennmoor Spokane Branch | 84 | 4 | 0.0476 |
| AUTO-STD | Fennmoor Stillwater Branch | 83 | 6 | 0.0723 |
| PL-STD | Fennmoor Bartlesville Branch | 79 | 8 | 0.1013 |
| MTG-30F | Fennmoor Lawton Branch | 79 | 3 | 0.038 |
| AUTO-STD | Fennmoor Kansas City Branch | 78 | 7 | 0.0897 |
| AUTO-STD | Fennmoor Oklahoma City Branch | 77 | 10 | 0.1299 |
| HELOC-STD | Fennmoor Lawton Branch | 75 | 3 | 0.04 |
| AUTO-STD | Fennmoor Norman Branch | 74 | 6 | 0.0811 |
| HELOC-STD | Fennmoor Spokane Branch | 74 | 2 | 0.027 |
| PL-STD | Fennmoor Wichita Branch | 73 | 4 | 0.0548 |
| AUTO-STD | Fennmoor Bartlesville Branch | 70 | 2 | 0.0286 |
| PL-STD | Fennmoor Stillwater Branch | 69 | 4 | 0.058 |
| PL-STD | Fennmoor Oklahoma City Branch | 65 | 5 | 0.0769 |
| AUTO-STD | Fennmoor Wichita Branch | 65 | 3 | 0.0462 |
| PL-STD | Fennmoor Norman Branch | 64 | 2 | 0.0313 |
| PL-STD | Fennmoor Omaha Branch | 57 | 5 | 0.0877 |
| AUTO-STD | Fennmoor Omaha Branch | 56 | 6 | 0.1071 |
| AUTO-STD | Fennmoor Lincoln Branch | 53 | 0 | 0 |
| PL-STD | Fennmoor Springfield Branch | 50 | 2 | 0.04 |

56 rows, the first 50 shown; 30 MiB billed.

## Q10. Does customer satisfaction vary with agent tenure?

| tenure | surveys | avg_csat |
|---|---|---|
| 1 to 3 years | 962 | 2.99 |
| 3 years or more | 4,374 | 3.00 |
| BPO (no hire date) | 2,953 | 2.99 |
| under 1 year | 437 | 2.86 |

4 rows; 0 MiB billed.

## Q11. How many customers use the mobile app each week?

| week | customers |
|---|---|
| 2026-03-29 | 10,097 |
| 2026-04-05 | 12,858 |
| 2026-04-12 | 12,886 |
| 2026-04-19 | 12,825 |
| 2026-04-26 | 12,897 |
| 2026-05-03 | 12,866 |
| 2026-05-10 | 12,844 |
| 2026-05-17 | 12,873 |
| 2026-05-24 | 12,870 |
| 2026-05-31 | 12,863 |
| 2026-06-07 | 12,830 |
| 2026-06-14 | 12,908 |
| 2026-06-21 | 12,914 |
| 2026-06-28 | 6,540 |

14 rows; 0 MiB billed.

## Q12. Contact details for an email campaign to affluent customers.

| cif_number | full_name | primary_email | segment |
|---|---|---|---|
| 0001000020 | Redbud Consulting | barbara.davis8@example.com | affluent |
| 0001000065 | Ethan Martinez | michael.tran100@example.com | affluent |
| 0001000080 | Jessica Young | aisha.patel128@example.com | affluent |
| 0001000088 | Susan Wright | david.scott143@example.com | private |
| 0001000099 | Wei Tran | mary.brown171@example.com | affluent |
| 0001000102 | Omar Ramirez | wei.moore177@example.com | affluent |
| 0001000107 | Wei Adams | mary.johnson186@example.com | affluent |
| 0001000118 | Mateo Martinez | sarah.campbell210@example.com | private |
| 0001000126 | Sarah Adams | robert.lewis227@example.com | affluent |
| 0001000134 | Sarah Lewis | mateo.davis245@example.com | affluent |
| 0001000163 | Jessica Ramirez | sarah.anderson300@example.com | affluent |
| 0001000167 | Robert Johnson | michael.young310@example.com | affluent |
| 0001000199 | Omar Lee | john.clark370@example.com | affluent |
| 0001000210 | Maria Hernandez | anh.martinez389@example.com | affluent |
| 0001000222 | Hannah Wright | ethan.thomas413@example.com | affluent |
| 0001000225 | Thomas King | elizabeth.baker418@example.com | affluent |
| 0001000255 | Susan Brown | joseph.green471@example.com | affluent |
| 0001000268 | Hannah Garcia | minh.tran502@example.com | affluent |
| 0001000269 | Sofia Patel | patricia.brown503@example.com | affluent |
| 0001000288 | Minh Garcia | noah.king539@example.com | affluent |
| 0001000291 | Mary Campbell | emma.johnson544@example.com | affluent |
| 0001000295 | Barbara Garcia | elizabeth.miller552@example.com | affluent |
| 0001000300 | Liam Ramirez | susan.tran563@example.com | affluent |
| 0001000312 | Jessica Taylor | chloe.kim584@example.com | affluent |
| 0001000355 | Ethan Davis | thomas.walker675@example.com | affluent |
| 0001000379 | Arjun Hernandez | sarah.thomas719@example.com | affluent |
| 0001000392 | Ethan Smith | minh.johnson742@example.com | affluent |
| 0001000411 | Joseph Davis | carlos.tran778@example.com | affluent |
| 0001000415 | Noah Garcia | linda.campbell788@example.com | affluent |
| 0001000439 | Thomas Thomas | robert.davis832@example.com | affluent |
| 0001000448 | Minh Ramirez | omar.patel850@example.com | affluent |
| 0001000456 | Noah Anderson | david.campbell870@example.com | affluent |
| 0001000457 | Mary Hernandez | sofia.hill873@example.com | private |
| 0001000461 | Arjun Taylor | arjun.hernandez883@example.com | affluent |
| 0001000479 | Anh Scott | carlos.hall919@example.com | affluent |
| 0001000483 | Omar Davis | mei.nguyen925@example.com | affluent |
| 0001000489 | Emma Lee | robert.anderson939@example.com | affluent |
| 0001000521 | James Lee | john.adams1004@example.com | private |
| 0001000529 | Olivia Rodriguez | lucas.jones1020@example.com | affluent |
| 0001000560 | Richard Moore | ethan.brown1080@example.com | private |
| 0001000570 | Noah Wilson | mary.wilson1100@example.com | affluent |
| 0001000574 | Lucas Lopez | michael.tran1108@example.com | affluent |
| 0001000589 | Maria Kim | mary.campbell1134@example.com | private |
| 0001000605 | Noah Thomas | aisha.allen1166@example.com | affluent |
| 0001000655 | Anh Williams | maria.martin1266@example.com | affluent |
| 0001000666 | Wei Jones | ethan.walker1287@example.com | affluent |
| 0001000689 | Omar Tran | wei.rodriguez1328@example.com | affluent |
| 0001000690 | Grace Kim | sarah.walker1329@example.com | affluent |
| 0001000696 | James Kim | sarah.martinez1342@example.com | affluent |
| 0001000698 | Mei Lewis | maria.thomas1347@example.com | affluent |

1,566 rows, the first 50 shown; 20 MiB billed.

## Q13. What is in the tables whose names start with CC?

| table_ | meaning | rows_ | first_ | last_ |
|---|---|---|---|---|
| legacy_edw.CC_EXPNS_MTHLY | cost center expense (legacy) | 8,800 | 2024-12 | 2025-02 |
| legacy_edw.CC_ACCT_MSTR | credit card accounts | 10,929 | 2008-01-01 | 2025-02-15 |
| gl_erp.CC_EXPENSE_SUMMARY | cost center expense (GL) | 11,000 | APR-26 | MAY-26 |
| legacy_edw.CC_TXN_HIST | credit card transactions | 1,580,988 | 2024-11-29 | 2025-02-28 |
| legacy_edw.CC_CALL_VOL_DLY | contact center call volume | 276 | 2025-07-01 | 2025-09-30 |
| legacy_edw.CC_AGENT_DLY | contact center agent activity | 14,000 | 2025-07-01 | 2025-09-30 |

6 rows; 0 MiB billed.

## Q14. Account closures by reason, deposits versus cards.

| account_family | reason | closures |
|---|---|---|
| CARD | PRODUCT_CHANGE | 208 |
| CARD | CUST_REQ | 204 |
| CARD | FRAUD | 198 |
| CARD | CHARGE_OFF | 197 |
| CARD | DORMANT | 169 |
| DEPOSIT | FRAUD | 441 |
| DEPOSIT | CUST_REQ | 430 |
| DEPOSIT | COMPETITOR | 429 |
| DEPOSIT | MOVED | 407 |
| DEPOSIT | DECEASED | 400 |
| DEPOSIT | DORMANT | 385 |
| DEPOSIT | FEES | 381 |

12 rows; 10 MiB billed.
