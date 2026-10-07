# The Cypher the page runs

One query to a file, `<section>/<name>.cypher`. The generators in `examples/fennmoor-bank/generate/` read them (`ui_queries.py`) to write each
section's data, and the page can show the same file, so what it shows is what made its numbers.

A file begins with comment lines: the **database** it runs on (`bigquery` is the semantic layer, `memory` what Virtual Graph reads fetched), its
**parameters**, if any, and what it **returns**. Neo4j ignores the comments, so the file is the query.

| Folder | Read by | Queries |
|---|---|---|
| `discovery/` | `ui_discovery.py` | the hierarchy, each table's group, the variables, the joins behind them, the joins kept out, the totals |
| `virtual/` | `ui_virtual.py` | the node labels and the relationship types the model made, with the variable each holds |
| `memory/` | `ui_memory.py` | each table's write days, and a remembered node's provenance |

What is not here: the tool's own Cypher stays in the `qlsc` module that uses it, as named constants (`src/qlsc/`), and the walk-through queries for Neo4j
Browser are `examples/fennmoor-bank/demo.cypher` (each one is tested). A query is added here when a generator or the page needs it.
