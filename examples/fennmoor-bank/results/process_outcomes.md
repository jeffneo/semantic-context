# Process abstraction, phase 2: the kinds of outcome

2032 conversations; the kinds were found by describing how each ended (its last turns and the agent's after-call note), embedding the descriptions and grouping them (similarity 0.8, resolution 0.5, kinds under 5 conversations folded into the nearest). Tuning slice: the first 600 by id; holdout: the rest.

## The holdout

| arm | kinds | against the planted outcomes: h / c / V | against what the text can show: h / c / V |
|---|---|---|---|
| described (the build) | 28 | 0.67 / 0.35 / **0.46** | 0.87 / 0.30 / **0.44** |
| raw note, no description | 29 | 0.42 / 0.23 / **0.30** | 0.51 / 0.18 / **0.27** |
| planted (ceiling) | 12 | 1.00 / 1.00 / **1.00** | 1.00 / 0.65 / **0.79** |

Rating against the planted favourability (1432 conversations): Spearman **0.75**; AUC for telling the cases that ended well (planted high) from the rest **0.92**; mean rating by planted favourability: high 4.3, medium 2.8, low 2.1, very-low 1.6

## The tuning conversations

| arm | kinds | against the planted outcomes: h / c / V | against what the text can show: h / c / V |
|---|---|---|---|
| described (the build) | 28 | 0.68 / 0.37 / **0.48** | 0.87 / 0.30 / **0.45** |
| raw note, no description | 29 | 0.44 / 0.25 / **0.31** | 0.50 / 0.18 / **0.27** |
| planted (ceiling) | 11 | 1.00 / 1.00 / **1.00** | 1.00 / 0.64 / **0.78** |

Rating against the planted favourability (600 conversations): Spearman **0.79**; AUC for telling the cases that ended well (planted high) from the rest **0.94**; mean rating by planted favourability: high 4.3, medium 2.6, low 2.1, very-low 1.7

## What each kind is made of (planted outcomes, the three commonest)

| kind | conversations | rating | planted outcomes |
|---|---|---|---|
| Account closed as requested | 211 | 3.4 | RESOLVED-FIRST-CONTACT 113, CLOSED-AFTER-SAVE-ATTEMPT 67, CLOSED-WITHSAVE-ATTEMPT 23 |
| Account balance provided, customer satisfied | 169 | 4.7 | RESOLVED-FIRST-CONTACT 165, RESOLVED-POLICY-BREACH 4 |
| Identity verified, account hold released | 154 | 4.1 | RESOLVED-FIRST-CONTACT 111, RESOLVED-POLICY-BREACH 28, FALSE-RESOLUTION 15 |
| Chargeback filed with provisional credit | 147 | 3.4 | RESOLVED-FIRST-CONTACT 72, PARTIAL 34, WRONG-FIX-COSTED 18 |
| Disputed charge transferred unresolved | 121 | 2.0 | TRANSFERRED 121 |
| Card blocked and replacement issued | 119 | 3.5 | RESOLVED-FIRST-CONTACT 80, PARTIAL 17, WRONG-FIX-COSTED 10 |
| Account closure averted by retention offer | 108 | 4.1 | RETAINED-WITH-OFFER 106, RETAINED-WITH-BREACH 2 |
| Escalated to supervisor, dispute unresolved | 98 | 2.0 | ESCALATED 95, TRANSFERRED 3 |
| Address updated, customer satisfied | 96 | 4.9 | RESOLVED-FIRST-CONTACT 94, RESOLVED-POLICY-BREACH 2 |
| Disputed fee waived, case settled | 94 | 4.2 | RESOLVED-FIRST-CONTACT 48, PARTIAL 32, WRONG-FIX-COSTED 8 |
| Closure request transferred, unresolved | 89 | 2.0 | TRANSFERRED 66, ESCALATED 23 |
| Card question answered, customer satisfied | 79 | 4.1 | RESOLVED-FIRST-CONTACT 76, RESOLVED-POLICY-BREACH 3 |
| Statement copy sent, customer satisfied | 70 | 4.8 | RESOLVED-FIRST-CONTACT 70 |
| Customer hung up before resolution | 66 | 1.3 | ABANDONED-FRUSTRATED 66 |
| Payment reapplied to correct account and date | 59 | 3.3 | RESOLVED-FIRST-CONTACT 38, FALSE-RESOLUTION 20, RESOLVED-POLICY-BREACH 1 |
| Payment processed on call, satisfied | 55 | 4.7 | RESOLVED-FIRST-CONTACT 53, RESOLVED-POLICY-BREACH 2 |
| Sent to merchant for disputed charge | 51 | 2.1 | RESOLVED-FIRST-CONTACT 39, PARTIAL 8, RESOLVED-POLICY-BREACH 4 |
| Fee waiver denied, repeat charge | 34 | 2.4 | RESOLVED-FIRST-CONTACT 17, FALSE-RESOLUTION 15, WRONG-FIX-COSTED 1 |
| Payment plan set up for disputed fee | 32 | 3.7 | RESOLVED-FIRST-CONTACT 28, FALSE-RESOLUTION 3, RESOLVED-POLICY-BREACH 1 |
| Autopay repaired, fee dispute unaddressed | 32 | 2.8 | RESOLVED-FIRST-CONTACT 23, FALSE-RESOLUTION 7, RESOLVED-POLICY-BREACH 2 |
| Charge not disputable, customer accepted explanation | 30 | 2.5 | RESOLVED-FIRST-CONTACT 28, FALSE-RESOLUTION 2 |
| Scam payment recall initiated, pending | 28 | 3.0 | RESOLVED-FIRST-CONTACT 18, RESOLVED-POLICY-BREACH 6, WRONG-FIX-COSTED 4 |
| Duplicate payment refunded, customer satisfied | 26 | 4.7 | RESOLVED-FIRST-CONTACT 26 |
| Fraud case opened, account secured | 19 | 3.7 | RESOLVED-FIRST-CONTACT 14, RESOLVED-POLICY-BREACH 4, PARTIAL 1 |
| Routing number location question answered | 13 | 5.0 | RESOLVED-FIRST-CONTACT 13 |
| Account alerts setup question answered | 11 | 4.7 | RESOLVED-FIRST-CONTACT 11 |
| Wire transfer fee question answered | 11 | 4.7 | RESOLVED-FIRST-CONTACT 11 |
| Joint owner info and form sent | 10 | 4.4 | RESOLVED-FIRST-CONTACT 8, RESOLVED-POLICY-BREACH 2 |

The planted outcomes, for scale: RESOLVED-FIRST-CONTACT 1156, TRANSFERRED 191, ESCALATED 132, RETAINED-WITH-OFFER 106, PARTIAL 92, RESOLVED-POLICY-BREACH 92, ABANDONED-FRUSTRATED 68, CLOSED-AFTER-SAVE-ATTEMPT 67, FALSE-RESOLUTION 62, WRONG-FIX-COSTED 41, CLOSED-WITHSAVE-ATTEMPT 23, RETAINED-WITH-BREACH 2.
