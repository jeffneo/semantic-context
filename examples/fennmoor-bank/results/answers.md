# Reference answers

Each gold question's hand-written reference query (`eval/reference/`), run against the filled estate. These are the answers execution accuracy scores against.

## Q01. Which contact centers see the most account cancellations, and what did each cost to run last year?

| site_name | closure_contacts | contacts | expense_2025 |
|---|---|---|---|
| Tulsa Contact Center | 3,564 | 51,737 | 71876887.16 |
| Spokane Contact Center | 1,861 | 26,214 | 71486853.56 |
| Manila BPO | 1,532 | 21,049 | 70736205.57 |

3 rows; 40 MiB billed.

## Q02. What is the churn risk of our high-balance customers?

| segment | customers | avg_churn_probability | high_risk |
|---|---|---|---|
| mass | 526 | 0.352 | 46 |
| mass_affluent | 183 | 0.344 | 17 |
| affluent | 71 | 0.338 | 5 |
| small_business | 41 | 0.354 | 3 |
| private | 14 | 0.38 | 1 |

5 rows; 0 MiB billed.

## Q02, also accepted (Q02.alt)

| cif_number | segment | total_deposit_balance | churn_probability |
|---|---|---|---|
| 0001011262 | mass | 826805.06 | 0.3743 |
| 0001000017 | mass_affluent | 639892.15 | 0.194 |
| 0001004392 | mass | 496371.64 | 0.2017 |
| 0001017544 | affluent | 376813.68 | 0.0374 |
| 0001000347 | mass | 368417.51 | 0.2123 |
| 0001000019 | small_business | 354613.82 | 0.0464 |
| 0001002790 | mass | 319605.69 | 0.8364 |
| 0001015146 | mass_affluent | 269395.77 | 0.0649 |
| 0001019465 | small_business | 265790.91 | 0.1563 |
| 0001010765 | mass | 265654.4 | 0.4916 |
| 0001000018 | mass | 260237.19 | 0.3869 |
| 0001021049 | mass_affluent | 259562.56 | 0.193 |
| 0001013424 | mass | 253275.12 | 0.0169 |
| 0001000020 | affluent | 252637.4 | 0.4303 |
| 0001002042 | mass | 249543.41 | 0.4517 |
| 0001007114 | mass | 247756.77 | 0.548 |
| 0001008504 | small_business | 243445.61 | 0.2181 |
| 0001008391 | mass | 238986.3 | 0.175 |
| 0001006538 | mass | 236653.34 | 0.2855 |
| 0001008223 | mass | 231598.75 | 0.3869 |
| 0001002862 | small_business | 231084.57 | 0.4078 |
| 0001000755 | affluent | 229538.77 | 0.4034 |
| 0001013905 | mass | 228928.05 | 0.3617 |
| 0001000913 | mass_affluent | 228679.07 | 0.2238 |
| 0001009881 | mass_affluent | 225929.76 | 0.0322 |
| 0001000272 | mass_affluent | 224958.66 | 0.2413 |
| 0001005974 | mass | 224142.39 | 0.5431 |
| 0001000105 | mass | 222727.41 | 0.581 |
| 0001003039 | affluent | 222319.49 | 0.5682 |
| 0001000499 | mass | 221478.21 | 0.5042 |
| 0001009347 | private | 214020.54 | 0.1474 |
| 0001011287 | mass_affluent | 213583.12 | 0.0644 |
| 0001010049 | mass_affluent | 212993.34 | 0.169 |
| 0001000400 | mass | 211797.41 | 0.5743 |
| 0001000926 | mass | 211533.67 | 0.2963 |
| 0001011697 | mass | 209343.03 | 0.044 |
| 0001005363 | mass | 207588.83 | 0.2553 |
| 0001002131 | mass | 202614.17 | 0.4737 |
| 0001000104 | affluent | 202452.21 | 0.2164 |
| 0001000030 | mass | 202318.19 | 0.5128 |
| 0001000253 | mass | 198584.59 | 0.5612 |
| 0001021675 | affluent | 195802.26 | 0.0996 |
| 0001000117 | mass | 191420.56 | 0.1738 |
| 0001009654 | mass | 189910.47 | 0.1009 |
| 0001002601 | mass_affluent | 187130.83 | 0.4139 |
| 0001004942 | mass | 182064.43 | 0.5781 |
| 0001000034 | mass | 181558.92 | 0.0416 |
| 0001000151 | mass | 180809.96 | 0.556 |
| 0001000080 | affluent | 178332.16 | 0.3745 |
| 0001002137 | affluent | 172603.34 | 0.3587 |

835 rows, the first 50 shown; 10 MiB billed.

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

45 rows; 0 MiB billed.

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

12 rows; 0 MiB billed.

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

| campaign_id | campaign_name | card_applications |
|---|---|---|
| 95bb449d-c3fe-8906-0ae6-0a312c378c38 | HELOC Rate Drop 1 | 610 |
| c69af579-f5fc-4d50-fbf7-73eb757003bf | Checking Bonus 300 2 | 283 |
| 56e42e9d-13b6-bc03-8795-81af25eea4c2 | Travel Rewards Launch 3 | 242 |
| a08d0379-c3bb-e335-40bb-e98465ff0394 | Card Activation Reminder 4 | 207 |
| 11a5f176-5b86-d245-1163-cd8d14fa3037 | Checking Bonus 300 5 | 184 |
| 3fdd2e92-8658-4da9-994e-43fd1cea25da | Card Activation Reminder 6 | 175 |
| 44c239c8-dbe5-9711-744e-478465fc96a4 | HELOC Rate Drop 8 | 166 |
| 761fd53d-a35f-4466-2b7a-c15681676293 | HELOC Rate Drop 7 | 159 |
| 6307e600-99ae-4a91-83e2-caf4fa187b49 | Savings Rate Alert 10 | 151 |
| e1f76d7e-fe51-cf49-4fb8-02c5f8771459 | Spring Cash Back 13 | 145 |
| 581b11d2-0000-3cda-5d29-a2e0a530931b | Travel Rewards Launch 12 | 135 |
| a17828a0-8346-518b-e982-2515f6530a61 | HELOC Rate Drop 14 | 129 |
| 017d6686-2fd7-a3c6-bab3-a4af0f1ae8db | Spring Cash Back 16 | 129 |
| 4cd20935-8619-8db5-fac2-2a31d7bfb7a7 | Travel Rewards Launch 9 | 128 |
| 684f7d51-235d-a3a1-f920-64c285123fc9 | Checking Bonus 300 20 | 126 |
| 00dd9efa-61e6-de50-3524-e95bfda32873 | Card Activation Reminder 11 | 122 |
| afde2b58-05a7-92b9-58d8-d3522d52f8bd | Travel Rewards Launch 21 | 116 |
| f849f2a8-caad-555b-1b24-8e354709b39b | Checking Bonus 300 26 | 114 |
| 2b5feb8a-943e-7e4c-84e9-e3041eabeed1 | Savings Rate Alert 24 | 103 |
| 9f585685-a2f0-607d-fb31-2d8ba2337de5 | HELOC Rate Drop 31 | 102 |
| 376ca2b2-cee6-7d23-76e3-1c2302f3eb0e | Savings Rate Alert 15 | 101 |
| 61396f7a-60e7-e27d-a369-b8fda0e6042f | Card Activation Reminder 18 | 100 |
| b986f0b7-4bac-f8e2-4a84-099ca4e1446f | HELOC Rate Drop 22 | 98 |
| b4c75df1-1250-150a-e06d-595335d4773d | HELOC Rate Drop 17 | 98 |
| d435899e-68ee-99d4-eb9d-55f9cf29a9ac | HELOC Rate Drop 28 | 96 |
| 33bb9a82-b5c3-bb49-bfa9-d9afd544a9ca | Digital Enrollment Nudge 33 | 94 |
| f647a82d-eaee-d097-141c-0fc74a032545 | Savings Rate Alert 29 | 93 |
| cf1385ed-fed2-dd84-6399-6e4811f133b6 | HELOC Rate Drop 30 | 93 |
| 35e7c83d-8897-6ddf-a51f-e4245e108d50 | HELOC Rate Drop 44 | 92 |
| d49334ed-dafd-6256-3659-4e35bba7850c | Digital Enrollment Nudge 25 | 91 |
| 1d3428aa-6e11-e41a-8164-040c57af7733 | Spring Cash Back 32 | 90 |
| 3a1f7a20-a9a8-cc7b-ed38-f08a356d0cd2 | Digital Enrollment Nudge 36 | 88 |
| 65333ce5-1e9e-0209-c3ea-d380b3a9893d | Checking Bonus 300 27 | 86 |
| 9e6926a3-d3e6-b41c-047a-771be5ec8a79 | Spring Cash Back 19 | 83 |
| c2f803ed-9bd7-5e1b-6ac4-473327f5edba | Spring Cash Back 23 | 82 |
| 821c35ac-b890-7c1c-c840-20862ca377d7 | Travel Rewards Launch 37 | 81 |
| 026e8d9b-8b3a-0d4a-ca5e-267b80c38f6e | Spring Cash Back 41 | 79 |
| 03fa34dd-3507-7950-b69c-75ef7bfe2366 | Digital Enrollment Nudge 39 | 79 |
| 7014d2cc-443d-98e3-28b6-f7131dd993ef | Digital Enrollment Nudge 34 | 77 |
| 82c04cd8-5a65-c271-3533-584ae1a97cee | Savings Rate Alert 42 | 77 |
| 321063b3-f7bc-9f92-70e8-ecc53b4d851b | Travel Rewards Launch 56 | 76 |
| d5b58dca-0ff8-db94-7edf-09520d88f82f | Digital Enrollment Nudge 50 | 76 |
| 5481d9af-8344-8e1f-9e8c-4757e7ae15ac | Digital Enrollment Nudge 66 | 76 |
| 254c75ba-56cc-785d-f731-837d15ce393a | HELOC Rate Drop 35 | 75 |
| 7377e150-88e6-bc03-90f2-0ebef228367f | Savings Rate Alert 78 | 74 |
| f60e253d-9b9f-ee3c-7906-d18f324deb31 | Checking Bonus 300 60 | 74 |
| 2ca3eead-7140-1121-8dae-1bc5f70cdf30 | Checking Bonus 300 55 | 74 |
| 47a3dbfa-9070-b98e-5797-9aa717a3df79 | Savings Rate Alert 43 | 73 |
| d65d9234-6c9c-9fa6-db70-6af77955b255 | HELOC Rate Drop 64 | 72 |
| 20cbc958-1cfa-0614-d3c3-72a6b60f6575 | Spring Cash Back 53 | 72 |

5,200 rows, the first 50 shown; 20 MiB billed.

## Q09. Loan delinquency rate by product and branch.

| product_code | branch_id | branch_name | open_loans | delinquent | delinquency_rate |
|---|---|---|---|---|---|
| MTG-30F | 101 | Fennmoor Topeka #101 | 95 | 3 | 0.0316 |
| HELOC-STD | 101 | Fennmoor Topeka #101 | 77 | 4 | 0.0519 |
| MTG-30F | 104 | Fennmoor Stillwater #104 | 49 | 2 | 0.0408 |
| MTG-30F | 113 | Fennmoor Boise #113 | 45 | 2 | 0.0444 |
| AUTO-STD | 101 | Fennmoor Topeka #101 | 44 | 5 | 0.1136 |
| HELOC-STD | 107 | Fennmoor Tulsa #107 | 40 | 3 | 0.075 |
| HELOC-STD | 104 | Fennmoor Stillwater #104 | 38 | 1 | 0.0263 |
| MTG-30F | 110 | Fennmoor Boise #110 | 36 | 1 | 0.0278 |
| MTG-30F | 107 | Fennmoor Tulsa #107 | 35 | 4 | 0.1143 |
| HELOC-STD | 110 | Fennmoor Boise #110 | 34 | 3 | 0.0882 |
| MTG-30F | 149 | Fennmoor Kansas City #149 | 32 | 1 | 0.0313 |
| HELOC-STD | 131 | Fennmoor Kansas City #131 | 31 | 2 | 0.0645 |
| MTG-30F | 134 | Fennmoor Bartlesville #134 | 31 | 2 | 0.0645 |
| PL-STD | 101 | Fennmoor Topeka #101 | 29 | 2 | 0.069 |
| MTG-30F | 122 | Fennmoor Boise #122 | 29 | 2 | 0.069 |
| AUTO-STD | 104 | Fennmoor Stillwater #104 | 26 | 1 | 0.0385 |
| PL-STD | 104 | Fennmoor Stillwater #104 | 25 | 0 | 0 |
| MTG-30F | 116 | Fennmoor Oklahoma City #116 | 25 | 0 | 0 |
| HELOC-STD | 140 | Fennmoor Wichita #140 | 25 | 1 | 0.04 |
| MTG-30F | 146 | Fennmoor Oklahoma City #146 | 25 | 2 | 0.08 |
| PL-STD | 107 | Fennmoor Tulsa #107 | 24 | 1 | 0.0417 |
| HELOC-STD | 128 | Fennmoor Norman #128 | 24 | 1 | 0.0417 |
| AUTO-STD | 107 | Fennmoor Tulsa #107 | 23 | 2 | 0.087 |
| HELOC-STD | 119 | Fennmoor Tulsa #119 | 23 | 1 | 0.0435 |
| MTG-30F | 128 | Fennmoor Norman #128 | 23 | 0 | 0 |
| HELOC-STD | 134 | Fennmoor Bartlesville #134 | 23 | 1 | 0.0435 |
| HELOC-STD | 146 | Fennmoor Oklahoma City #146 | 23 | 3 | 0.1304 |
| HELOC-STD | 113 | Fennmoor Boise #113 | 22 | 4 | 0.1818 |
| HELOC-STD | 155 | Fennmoor Topeka #155 | 22 | 2 | 0.0909 |
| MTG-30F | 119 | Fennmoor Tulsa #119 | 21 | 1 | 0.0476 |
| HELOC-STD | 122 | Fennmoor Boise #122 | 21 | 1 | 0.0476 |
| HELOC-STD | 125 | Fennmoor Stillwater #125 | 21 | 1 | 0.0476 |
| MTG-30F | 125 | Fennmoor Stillwater #125 | 21 | 1 | 0.0476 |
| MTG-30F | 131 | Fennmoor Kansas City #131 | 21 | 1 | 0.0476 |
| MTG-30F | 137 | Fennmoor Tulsa #137 | 21 | 1 | 0.0476 |
| HELOC-STD | 149 | Fennmoor Kansas City #149 | 21 | 0 | 0 |
| MTG-30F | 161 | Fennmoor Omaha #161 | 20 | 3 | 0.15 |
| MTG-30F | 188 | Fennmoor Wichita #188 | 20 | 1 | 0.05 |
| HELOC-STD | 212 | Fennmoor Boise #212 | 20 | 0 | 0 |
| AUTO-STD | 113 | Fennmoor Boise #113 | 19 | 0 | 0 |
| AUTO-STD | 134 | Fennmoor Bartlesville #134 | 19 | 1 | 0.0526 |
| PL-STD | 122 | Fennmoor Boise #122 | 18 | 2 | 0.1111 |
| MTG-30F | 167 | Fennmoor Lincoln #167 | 18 | 0 | 0 |
| MTG-30F | 197 | Fennmoor Omaha #197 | 18 | 0 | 0 |
| HELOC-STD | 224 | Fennmoor Bartlesville #224 | 18 | 2 | 0.1111 |
| MTG-30F | 284 | Fennmoor Lawton #284 | 18 | 0 | 0 |
| AUTO-STD | 125 | Fennmoor Stillwater #125 | 17 | 3 | 0.1765 |
| HELOC-STD | 152 | Fennmoor Oklahoma City #152 | 17 | 0 | 0 |
| MTG-30F | 152 | Fennmoor Oklahoma City #152 | 17 | 2 | 0.1176 |
| HELOC-STD | 167 | Fennmoor Lincoln #167 | 17 | 0 | 0 |

683 rows, the first 50 shown; 30 MiB billed.

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

1,566 rows, the first 50 shown; 0 MiB billed.

## Q12, also accepted (Q12.alt)

| cif_number | full_name | primary_email | segment |
|---|---|---|---|
| 0001000020 | Redbud Consulting | barbara.davis8@example.com | affluent |
| 0001000065 | Ethan Martinez | michael.tran100@example.com | affluent |
| 0001000080 | Jessica Young | aisha.patel128@example.com | affluent |
| 0001000099 | Wei Tran | mary.brown171@example.com | affluent |
| 0001000102 | Omar Ramirez | wei.moore177@example.com | affluent |
| 0001000107 | Wei Adams | mary.johnson186@example.com | affluent |
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
| 0001000461 | Arjun Taylor | arjun.hernandez883@example.com | affluent |
| 0001000479 | Anh Scott | carlos.hall919@example.com | affluent |
| 0001000483 | Omar Davis | mei.nguyen925@example.com | affluent |
| 0001000489 | Emma Lee | robert.anderson939@example.com | affluent |
| 0001000529 | Olivia Rodriguez | lucas.jones1020@example.com | affluent |
| 0001000570 | Noah Wilson | mary.wilson1100@example.com | affluent |
| 0001000574 | Lucas Lopez | michael.tran1108@example.com | affluent |
| 0001000605 | Noah Thomas | aisha.allen1166@example.com | affluent |
| 0001000655 | Anh Williams | maria.martin1266@example.com | affluent |
| 0001000666 | Wei Jones | ethan.walker1287@example.com | affluent |
| 0001000689 | Omar Tran | wei.rodriguez1328@example.com | affluent |
| 0001000690 | Grace Kim | sarah.walker1329@example.com | affluent |
| 0001000696 | James Kim | sarah.martinez1342@example.com | affluent |
| 0001000698 | Mei Lewis | maria.thomas1347@example.com | affluent |
| 0001000710 | Mateo Wilson | maria.johnson1368@example.com | affluent |
| 0001000750 | Redbud Consulting | jessica.hill1453@example.com | affluent |
| 0001000755 | Robert Hill | thomas.nguyen1459@example.com | affluent |
| 0001000757 | Sofia Adams | aisha.wilson1464@example.com | affluent |
| 0001000793 | James Lewis | liam.young1537@example.com | affluent |
| 0001000838 | Liam Campbell | lucas.young1629@example.com | affluent |

1,311 rows, the first 50 shown; 20 MiB billed.

## Q13. What is in the tables whose names start with CC?

| table_ | meaning | rows_ | first_ | last_ |
|---|---|---|---|---|
| legacy_edw.CC_EXPNS_MTHLY | cost center expense (legacy) | 8,800 | 2024-12 | 2025-02 |
| gl_erp.CC_EXPENSE_SUMMARY | cost center expense (GL) | 11,000 | APR-26 | MAY-26 |
| legacy_edw.CC_ACCT_MSTR | credit card accounts | 10,929 | 2008-01-01 | 2025-02-15 |
| legacy_edw.CC_CALL_VOL_DLY | contact center call volume | 276 | 2025-07-01 | 2025-09-30 |
| legacy_edw.CC_TXN_HIST | credit card transactions | 1,580,988 | 2024-11-29 | 2025-02-28 |
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

12 rows; 0 MiB billed.
