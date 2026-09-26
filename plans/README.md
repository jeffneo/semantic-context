# plans/

Plans agreed before the work starts, one file per piece of work, named `YYYY-MM-DD-topic.md`. This repo
is built with AI agents, and a plan here is the shared record of what was agreed and why: the next
session reads it instead of reconstructing intent from the code.

A plan says what problem it solves, what will change, what will not, how it will be checked, and the
decisions it depends on. Keep its status line current (`proposed`, `agreed`, `in progress`, `done`).

When the work is done, whatever stays true moves into [docs/design.md](../docs/design.md) (a decision,
a parameter, a limit), and the plan stays here as the record of how it came about. Plans are history;
`docs/` is the current truth.
