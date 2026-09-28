You name the computations in {business}'s data warehouse: what the {kind} computes from its columns,
again and again, found in the queries it runs. Each has a kind:
- measure: an aggregate the business reports (card spend, confirmed-fraud share), with the filters that
  always come with it;
- dimension: a grouping the business derives rather than stores (a month from a posting date, an age
  bucket from tenure);
- population: a set of rows the business filters to (marketable affluent customers, voice calls).

For each you get the kind, the expression over its table's columns, the filters and grouping it comes
with, the tables, the names queries give it, and how much it is used. Give:
- name: what it is, in 2 to 6 plain words a business analyst would use (Title Case). Not a column name,
  not SQL. For a measure, what is measured ("Card Purchase Spend"); for a population, who or what is in
  it ("Affluent And Private Customers"). Name what is computed, not an instance of it: leave a filter's
  particular value (a site, a month, a campaign) out of a measure's name unless the measure only
  makes sense for it, and leave the grouping out ("Call Abandon Rate", not "Call Abandon Rate By
  Site").
- description: one sentence saying what it computes and over what, including what the filters restrict
  it to, from the evidence only.
Use only the evidence given.
