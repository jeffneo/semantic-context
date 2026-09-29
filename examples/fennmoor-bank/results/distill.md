# Memory: skills distilled from the agents' experience

Phase 4 of the memory plan (plans/2026-09-29-context-memory-model.md). A simulated record:
- two patterns that repeat and work: marketing's customer-meeting preparation, 5 sessions; risk's review, 4;
- one that repeats and fails: rated wrong, 3 sessions;
- two one-offs.

`qlsc distill` groups the tasks by what they did and read (Leiden over their similarity), and proposes a skill from each group that repeats and succeeds. A person approves one. It's then offered to new tasks that fit, measured as they follow it, and retired when it stops working.

**13 of 13 checks passed.**

| check | result |
|---|---|
| skills for A and B, and no other | ok |
| no value of the evidence in any skill | ok |
| each skill ABOUT the tables its steps read | ok |
| distilling again changes nothing | ok |
| contact-center may not approve B | ok |
| marketing approves A, once | ok |
| a new A-like request of marketing's is offered A | ok |
| contact-center's same request is offered nothing | ok |
| B, proposed, is offered to no one | ok |
| 2 sessions offered A follow it and succeed | ok |
| 2 more that follow it fail, and A is retired | ok |
| a retired skill is offered to no one | ok |
| a reader sees how many tasks a skill came from, not which | ok |

## Skill A: Review customer holdings and recent card spending

Gathers context on a customer's relationship and analyzes their recent card transaction patterns by merchant category. Use this to prepare for customer meetings with insights into their banking behavior and spending habits.

Trigger: When you need to prepare for a customer meeting and want to know what products they hold and how they've spent on their cards by merchant category in a recent period.

1. recall the Customer's context
2. ask Card Purchase Spend by dim_merchant.category_group where fct_card_transactions.customer_key = ? over a period of fct_card_transactions.post_date

About: `fennmoor-dw.dw_core.dim_customer`, `fennmoor-dw.dw_core.dim_merchant`, `fennmoor-dw.dw_core.fct_card_transactions`

## Skill B: Review customer risk and deposit activity

Retrieves a customer's profile context and summarizes their deposit transactions by type over a recent period to assess risk exposure. Used to evaluate customer financial activity and patterns for compliance or credit review purposes.

Trigger: When you need to conduct a risk review of a customer by examining their background and recent deposits broken down by transaction type.

1. recall the Customer's context
2. ask SUM(fct_deposit_transactions.amount) by fct_deposit_transactions.transaction_type where fct_deposit_transactions.customer_key = ? over a period of fct_deposit_transactions.posted_date

About: `fennmoor-dw.dw_core.dim_customer`, `fennmoor-dw.dw_core.fct_deposit_transactions`
