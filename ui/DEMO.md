# Running the demo in five minutes

For whoever is at the keyboard. This is a list of things to do and the points to make at each, not a script: say it your own way. About 5 minutes if you keep to it. The stops
marked **(cut)** are the ones to shorten or skip when you are short of time.

## Things to get right

- It is a **reference architecture, not a product.** Say so early and don't walk it back. Best practices are still being worked out with early customers.
- **Virtual Graph is in public preview.** Don't call it generally available.
- "Interactive" is better than "real-time." Some of the examples involving LLMs or virtual graph take seconds rather than milliseconds.
- It reads **BigQuery** today. One **synthetic** estate. It could work with Snowflake or others as well.
- Every number below is on the page or in the evaluation results. Use these, not others.

## 1. The idea (about 30 s). Landing page

**Do:** stay on the landing page; point at the architecture diagram; then click **Example**.

- Everyone wants more from AI, and the data to do it is already there, in warehouses nobody fully understands. The hard part is getting the right context to the right agent at the right
  time. That is the layer this explores: **Context Engine**.
- Walk the diagram once: agents at the top, the warehouse along the bottom. The engine **reads the warehouse's query log and discovers the semantic layer itself**: what things mean and
  how they join.
- The **virtual graph** answers "do we have to copy all this data?": no. It turns Cypher into SQL, runs it in the warehouse, and returns a graph.
- **Agent memory** keeps what an agent fetched and did: so it can be audited, and so repeat work is fast. All three sit in one composite database, and **the warehouse stays the rulebook
  for who sees what.**

## 2. The estate (about 20 s). "The scenario" and "The warehouse"

**Do:** scroll to the warehouse map; click a table tile to open its schema.

- Fennmoor Bank, a fictional regional bank: **3 projects, 43 datasets, 323 tables and views, 315,729 queries in 90 days**, and none of it documented.
- A table's schema tells you the columns, not what they mean. Meaning is what the engine has to find.

## 3. Discovering the meaning (about 45 s). "Discovering the semantic layer"

**Do:** show the funnel; open "The tables, regrouped by meaning"; then open the live control and run **the map of the business**; then scroll to the variables.

- Input was the query log and the catalog, **nothing else**. 315,729 queries boil down to **109 groups of things the business reads together** (15 sub-areas, 4 broad areas).
- Regrouping the tables by how they are _used_, not how they are filed, is the point. The live run is the real semantic layer, not a picture.
- The key idea is the **join**: when a query joins two columns, they are the same real-world thing. We call that a **variable**. _Customer key_ turns up in **26 tables**, found from the log
  alone.
- Compare with a modelling project: months of work, and two teams draw two maps. This is repeatable and comes from real usage.

## 4. A graph over live rows (about 35 s). "Generating the Virtual Graph schema"

**Do:** show the two pictures side by side; click a table to see what it came from; open the live control and run **a customer's accounts and their products**.

- The variables become the graph schema, which you would normally design by hand. Pick a table and you see what it was derived from.
- The live run is a customer's accounts and products, and **every row is coming from the warehouse right now**. Nothing was copied, nothing to keep in sync.

## 5. Routing a request (about 35 s). "Routing a request"

**Do:** show the ladder; open the live control and run **Card spend by customer segment last quarter**.

- A plain rule, not a model, picks the cheapest route that can answer: **memory** first (milliseconds, no model), then **precedent** (the log has seen this kind of question), then SQL compiled
  from the semantic layer, Cypher over the virtual graph, and free SQL last.
- Point at what the run shows: which tables it picked, that the joins are written in code so it **cannot invent one**, the answer, and **what it cost**.

## 6. Memory (about 50 s). "Promoting results to memory"

**Do:** open the live control on the first memory part. The page **chose a customer for you when it loaded** (shown above the query, the same one in every memory control; "choose another" changes it). Run "Is this customer remembered?" (zero),
run the recall (about 6 seconds), run the check again (one), then run the recall again (milliseconds). Then show the economics chart.

- A result from the virtual graph can be **promoted into memory** as a context shape: a customer keeps its accounts, calls and branches; a branch keeps less. Each fact records how long it
  is good for. (Fetched rows are kept six hours, then swept; the record of what an agent did is kept.)
- The demonstration is the sequence: not there, **first recall reads the warehouse (about 6 s)**, now it is there, **second recall is milliseconds with nothing sent to the warehouse.**
- Across 50 questions a repeat took about **45 ms against about 700 ms** from the warehouse, and memory **pays for itself after about 8 questions**.

## 7. Auditing the agent (about 25 s). "What the agent did, auditable" **(cut)**

**Do:** open "What the agent did, auditable"; pick a conversation; switch the trace on; expand one tool call; then open the live control and run **why an agent decided**.

- Knowledge graphs should make agent behavior **auditable**, and this is that: each message, the tool calls it caused, what the agent learned, and the decision with its reasons.
- It is all in the graph, so **an audit is just a query**. The live run follows a decision back to its evidence. Say plainly that memory stores no hidden reasoning, only what is in the graph.

## 8. Does it work (about 20 s). "Accuracy at full scale" **(cut)**

**Do:** show the chart; open "Before you quote these".

- **186 questions with known answers**, mostly from queries the bank really ran, put four ways: the whole schema in the prompt gets about **two thirds** right and does not fit a real
  warehouse; the engine with an agent that can ask a clarifying question gets about **ninety percent**.
- Be upfront: **one synthetic estate**, and about half the questions repeat earlier ones. "Before you quote these" says so on the page.

## 9. Governed by the warehouse (about 40 s). "Row-level security..."

**Do:** open the live control on "The same question, three principals", run **customers in each state** as **admin**, then switch **Run as** to **risk** and run it, then to
**contact-center** and run it.

- None of this works unless it respects permissions. A **gateway** works out who is asking and signs that identity into the query; the pass-through hands it to BigQuery, which runs it **as
  that person**, so **its own row-level policies decide what comes back**.
- Same question, three answers: administrator **8 states**, the risk team **2** (all the warehouse lets them see), the contact center **nothing**, and the error **does not even say whether the
  data exists**.
- It was checked: **60 questions across three people, no leaks**, and then the gateway was broken on purpose **four ways, and every break was caught.**

## 10. Close (about 15 s)

**Do:** scroll back to the top.

- It is all in a GitHub repository and it reads BigQuery today.
- Ask what they face moving AI into production, and how this would fit their warehouse. Give them the contact shown in the page header.

## If something goes wrong

- **A live run is slow the first time.** Say what it is doing (it is asking BigQuery) and carry on; run it again if needed.
- **A live run says it "could not be completed".** For the contact center that is the point of stop 9. Anywhere else, run it again once; the page's examples are the only things the server will run,
  so there is nothing to type or fix.
- **The server is not running** (local): `scripts/stack up`. The page itself still reads without it; only the live controls need the server.
- **Short of time:** drop stops 7 and 8, and say the accuracy numbers in one sentence from stop 8.

## Likely questions

- _Do we have to copy our data?_ No: the virtual graph reads it where it is, through the warehouse's own permissions.
- _Does it need a data model first?_ No: it is discovered from the query log and the catalog, then aligned to a designed model if you have one.
- _Which warehouses?_ BigQuery today; nothing else has been tested.
- _Is it a product?_ A reference architecture, built with early customers.
