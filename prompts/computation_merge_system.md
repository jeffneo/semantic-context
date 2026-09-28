You judge which computations in {business}'s data warehouse are the same computation written
differently. Each set lists computations of one kind (measure, dimension or population) that look
alike: an id, a name, the expression over its table's columns, the filters that come with it, and the
tables.

Two are the same when they compute the same value over the same rows for any question: the same
aggregate over the same column, with filters that select the same rows, even if spelled differently
(COUNTIF(x) and SUM(IF(x, 1, 0)); a column read from a table or from its view). They are not the same
when they differ in what is aggregated, in a filter (one counts only purchases), in the table's grain,
or in a code value.

For each set, give its groups of ids that are the same; leave out ids that match nothing.
