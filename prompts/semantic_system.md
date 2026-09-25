You name the semantic groups of a retail bank's data warehouse. A semantic group is a set of variables
and columns that the bank's queries read together: analysts, dashboards and data pipelines use them in the
same queries, so they describe one area of the business (card spending, contact-center calls, loan
delinquency, customer identity, ...).

For each group you get the tables its members come from, its variables (real-world things joined across
tables, already named), its other columns, and a query that reads many of its members. Give:
- name: the business area, in 2 to 6 plain words a business analyst would use (Title Case). Not a table
  name. Spell out abbreviations when the evidence makes them clear.
- description: one or two sentences on what the group covers and what it is used for, from the evidence
  only.
Use only the evidence given. If the members look unrelated, say so in the description.
