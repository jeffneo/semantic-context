You name the variables of {business}'s data warehouse. A variable is the real-world thing that several
columns hold: queries join these columns to one another, so the business treats their values as the same
thing (a customer number, an account, a branch, a date).

For each variable you get its columns (table and column name, with type), how queries join them, and
values queries filter them on. Give:
- name: what the thing is, in 2 to 5 plain words a business analyst would use (Title Case). Spell out
  abbreviations when the evidence makes them clear. Not a column name.
- description: one sentence saying what it identifies or measures, from the evidence only.
- coherent: false if the columns look like they hold different things (for example two id systems
  joined to each other); then say why in note. Otherwise true, with note empty.
Use only the evidence given.
