#!/bin/sh
# Rebuild the graph from work/ end to end. extract.py (BigQuery) is run separately,
# only when the log or catalog changes. The parser service must be up.
set -e
cd "$(dirname "$0")/.."
uv run --quiet pipeline/parse_log.py "$@"
uv run --quiet pipeline/load_graph.py --reset
uv run --quiet specs/tools/score.py --only-m1   # validates the bottom layer: parse health, joins, lineage
uv run --quiet pipeline/variables.py            # WCC over joined columns -> named Variables; the rest :Unjoined
uv run --quiet pipeline/cluster.py              # Leiden over co-read Variable|Unjoined -> named :Semantic groups (level 1)
uv run --quiet pipeline/hierarchy.py            # embed, K_SIM kNN, Leiden per level -> Semantic levels 2..top
# The remaining upper stages (actors, detect, topology, semantics, guide, views) read the old model and
# are being rebuilt on the 7-label bottom layer; their M1-M6 output is in the `semanticlayer` database.
