You name the node labels and relationship types of a graph model over {business}'s data warehouse.
Each node label stands for the rows of one warehouse table; each relationship type stands for a column
in one table that points at the rows of another. You get the tables (with the business area the
{kind}'s queries place them in, and the identifier that keys them) and the relationships (which table
points at which, through which column). Give:
- label: what one row is, in PascalCase, singular, 1 to 3 words: Customer, Account, CardTransaction,
  ContactCenterSite. Not the table name with its prefix (no Dim, Fct, Int).
- type: what the pointing row has to do with the row it points at, in UPPER_SNAKE_CASE, 1 to 3 words,
  read from start to end: (Account)-[:HELD_BY]->(Customer), (CardTransaction)-[:CHARGED_TO]->(Account).
  Every type must be different from every other type, even between different pairs of labels.
Every label must be different from every other label. Use only the evidence given.
