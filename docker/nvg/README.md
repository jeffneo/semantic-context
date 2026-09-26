# docker/nvg/

JDBC drivers for the Neo4j Virtual Graph instance (`docker compose --profile vg up -d neo4j-vg`). Not in
git; download them here. Virtual Graph loads drivers from `NEO4J_HOME/lib`, one mount per jar.

```bash
curl -L -o docker/nvg/google-cloud-bigquery-jdbc-1.0.0-all.jar \
  https://repo.maven.apache.org/maven2/com/google/cloud/google-cloud-bigquery-jdbc/1.0.0/google-cloud-bigquery-jdbc-1.0.0-all.jar
```

Credentials: Virtual Graph's BigQuery driver reads one JSON credentials file. Make one that acts as the
estate's service account, in a gcloud directory of its own so your default credentials stay untouched,
and point `VG_CREDENTIALS` in `.env` at it:

```bash
CLOUDSDK_CONFIG=$HOME/.config/qlsc-vg gcloud auth application-default login \
  --impersonate-service-account=<service-account>@<project>.iam.gserviceaccount.com
```

Composite database: the semantic layer and the virtual graph in one query. Both constituents are remote
aliases, which need bolt TLS on both instances (`docker/tls/README.md`) and the keystore in
`docker-compose.yml`. A local alias to the virtual graph is accepted but never resolves, a Virtual
Graph bug. On `neo4j-vg`'s system database, with the password as `$pw`:

```cypher
CREATE COMPOSITE DATABASE fennmoor;
CREATE ALIAS fennmoor.semantic FOR DATABASE bigquery AT 'neo4j+ssc://neo4j:7687' USER neo4j PASSWORD $pw;
CREATE ALIAS fennmoor.rows FOR DATABASE neo4j AT 'neo4j+ssc://localhost:7687' USER neo4j PASSWORD $pw;
```

A subquery into `fennmoor.rows` can't import variables yet (`CALL (x) { USE fennmoor.rows ... }` is
rejected); pass values as parameters on a second query instead.
