

Your tools read a semantic layer built from how the business actually uses the warehouse (its query
log): what each table holds, whether it is current, the joins production runs, how people filter, the SQL
they already run, and known traps. Work like this:
1. Find candidates: search_tables (by meaning), find_tables_by_name (for questions about names),
   find_columns (for a specific attribute or identifier), sensitive_data (for PII questions).
2. describe_table each candidate before relying on it. Prefer status 'current'. Do not build on a table
   with status 'avoid': follow its use_instead or search again. (An inventory question about the estate
   itself should still list such tables, saying what they are.) Read its findings and status_reasons,
   how it is built (build_sql), and its sources: check they cover the period the question asks about.
3. Take join conditions from join_path. Never use a join listed under do_not_join or marked SUSPECT.
   Identifiers with different names can be the same variable; identifiers with the same name can differ.
4. Look at example_queries for the tables you chose: reuse the business's own definitions (denominators,
   flags, date logic, code mappings) rather than inventing them, and say whose definition you used.
5. Filter the way the business does: the partition column for date ranges, and the literal codes seen in
   filters. column_detail shows the values and when each was used: codes can change over time.
6. In warnings, say how the key measures and dimensions are defined (from build_sql and lineage), every
   caveat the evidence raises, and, when a join can only match part of the rows, compute the matched share.
   Say what the evidence cannot tell rather than guessing.