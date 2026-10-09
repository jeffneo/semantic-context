# What memory keeps, and for how long: a retention policy

Status: decided and built (2026-10-08). Uniform for local and hosted: six hours for fetched rows, the audit record kept. The sweep is `qlsc memory sweep` (`memory.py`, tests/test_memory_sweep.py);
`scripts/stack up` runs it once; hosted, a Cloud Run job fires it hourly (deploy/gcp/terraform/run.tf). The customer choice is `/api/pick` in the demo server.

## Why

Memory keeps two different things, and has no rule for either. Measured on the example's memory database (130,000 nodes):

| Kind | What | Size | Time on it | Today |
|---|---|---|---|---|
| **Fetched rows** | copies of warehouse rows: transactions, accounts, customers, merchants, agents, branches, calls | ~127,000 nodes | `fetched_at`, `holds_until` | `holds_until` makes a row *stale* (never read as fresh) but it is never deleted |
| **The audit record** | Steps (who read or asked what, when), Conversations, Messages, Tasks, Decisions, learned Facts, Skills, Entities | ~2,500 nodes | `recorded_at`, `owner` | kept for ever, by design: this is what makes an agent's behavior auditable |
| Stubs of the layer | Table, Column, Computation | ~120 | none | follow the layer |

The two want opposite things. A fetched row is a copy that has left the warehouse's row policies and column rules, so it should not outlive its use. The audit record
is the reason the database exists. Step results are short (13 to 130 characters on average): the audit record does not copy rows, so deleting the rows does not
hollow it out.

## The policy

1. **Fetched rows expire.** A node with `fetched_at` is deleted when it is older than `memory.retain.fetched_days` (default 30). A fetch re-stamps every node it
   touches, so a row a live context still uses is as young as that context. `holds_until` keeps meaning *fresh*; retention is how long a stale copy may sit.
   Deleting an anchor removes its context: the next `recall` finds none and fetches again, as it does today for a stale one.
2. **The audit record is kept** (`memory.retain.audit_days: null`). Set to a number, a *whole* conversation older than that goes, with its Messages, Tasks, Steps and Decisions,
   and the Facts only it relied on; standalone Steps (a `recall` or `ask` outside a conversation) go on their own age. Skills and Entities are never deleted by age
   (a Skill has its own retirement). A conversation is never cut in half.
3. **Every sweep leaves a Step** (`tool: sweep`, the settings and the counts it removed), so deletion is as auditable as reading, and it ages with the audit class.
4. **Reads need not wait for a sweep.** A row past its retention is not read; the sweep is what frees it.

## How it is enforced: a sweep command, not triggers

Not `apoc.trigger`. A trigger fires on a write, and retention is about the passage of time, so something would still have to run on a clock; it runs inside
unrelated transactions (the cost and the surprise land on whoever wrote last); it cannot be run as a dry run or tested on a copy; and APOC is not in the images the
deployment runs (the page also refuses `apoc.*`). I believe APOC's own TTL procedures are in the Extended package, which is not here either; I have not checked.

Instead `qlsc memory sweep [--dry-run] [--as-of DATE]`: one parameterized Cypher per class, deleted in batches (`CALL { … } IN TRANSACTIONS`), the counts printed, idempotent, safe beside
a `recall`. It reads its settings from `defaults.yaml` like everything else, and a deployment overrides them (`QLSC_OVERRIDES`).

Where it runs: on the laptop, once whenever `scripts/stack up` starts, and by hand; hosted, as a Cloud Run **job** (the demo image, command `qlsc memory sweep`) fired by Cloud
Scheduler every hour: two more Terraform resources. The hosted setting is short (`fetched_days: 0.25`, six hours), so what visitors leave behind goes the same day.

## The hosted memory panel: a customer of your own

Today the preset names one customer (0001000033), so every visitor recalls the same one and sees the previous visitor's context. With presets only, the key cannot be
typed, so the preset asks the server to *choose*: a customer with calls and card activity (read from the virtual graph, once per process) who has no remembered context
in memory, so each visitor's first recall is a real fetch, and the retention above expires it. One preset, one rule in the server; the key shown is the one chosen.

## Not in this plan

Clearing the older duplicate recordings of the example conversations (two sets, one from the converse evaluation); that waits for your approval, and a re-record.
A different policy for the *warehouse's* data is the warehouse's business.

## Decisions (made 2026-10-08)

1. **Six hours, for local and hosted alike** (`memory.retain.fetched_days: 0.25`); the audit record kept (`audit_days: null`, no default age).
2. **The sweep runs on a schedule hosted** (a Cloud Run job, hourly, by Cloud Scheduler) **and on `scripts/stack up` locally.**
3. **The customer is chosen as above**, at random, not from a fixed list: customer_360's customers with card transactions and contact-centre contacts in the last 90 days (500, in a
   deterministic spread), minus those memory holds. A recall or an example's `$customer` may name any customer of that pool, so every instance agrees without sharing state.

## Checked by

Built and checked: a test over a scratch memory database with rows and conversations of known ages: what expires, what stays, a conversation whole or gone, the sweep's own Step, a dry run that
deletes nothing. Then the memory evaluation (`eval/memory.py`), since nothing it reads fresh may disappear.
