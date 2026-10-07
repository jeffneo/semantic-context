// Database: bigquery (the semantic layer)
// How much the build holds: query shapes (and those from the log), join keys, variables, the columns that are joined, and all columns.
RETURN count { (:QueryShape) } AS shapes, count { (:QueryShape {origin: 'log'}) } AS logShapes, count { (:JoinKey) } AS joinKeys, count { (:Variable) } AS variables,
       count { (:Column)-[:IS]->(:Variable) } AS joined, count { (:Column) } AS columns
