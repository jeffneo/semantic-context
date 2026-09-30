The query ({who}; run {jobs} times in the log):
{sql}

First decide whether it serves a business consumer: a question someone in the business asks, or a
report, dashboard or process step that uses its answer. Not business: a write or load step, a data test
or freshness check, a schema or metadata lookup, a tool's own bookkeeping, a sample or row count run to
look at a table.

If it is business, write three requests it answers, each as its asker would send it:
- two questions, by two different askers (say who: a role), phrased differently;
- one task: the step of a business process that ran this query, as an AI agent carrying out that process
  would ask for it (say which process).
