The question the agent asks the data service: {question}

The query that answers it exactly as the process needs it:
{sql}

Write the agent's working state at this step. The agent knows its process, not the business's data: it
never knows which table, view, summary, extract, system or feed holds what, nor how records are matched
or joined, nor which records have a match elsewhere. Say nothing about where data comes from or how it
is put together; say only what the process itself has settled and what it needs.
- process: the business process it is running, and its goal
- step: the step it is on, and what it needs the data for
- established: what the process has already settled, one item each: the period under review, with its
  first and last days as the query has them; the business definitions it uses (what counts as high
  risk, which version of a score, which kinds of transaction count, how a week starts); the population
  in scope, in business terms (which customers, accounts, sites)
- next_step: the step that uses the result
- needs: what that step needs from the result, one item each: one row per what, which figures, how
  they are ordered or limited

Nothing the query doesn't do.
