The question the agent asks the data service: {question}

The query that answers it exactly as the process needs it:
{sql}

Write the agent's working state at this step:
- process: the business process it is running, and its goal
- step: the step it is on, and what it needs the data for
- established: what the process has already settled that bears on the data, one item each: the period
  under review, with its first and last days as the query has them; the definitions the process uses
  (which version of a score, which kinds of record count, how a week starts); the population in scope
- next_step: the step that uses the result
- needs: what that step needs from the result, one item each: one row per what, which figures, which
  rows are kept (those with no match elsewhere too, or not), how they are ordered or limited

Nothing the query doesn't do.
