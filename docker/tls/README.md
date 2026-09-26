# docker/tls/

A self-signed certificate for bolt on the local Neo4j instances. Bolt TLS is `OPTIONAL`, so plain
`neo4j://` and `bolt://` clients keep working; it exists because a remote database alias (how a
composite database on `neo4j-vg` reaches the semantic layer, and its own virtual graph) accepts only
`neo4j+s` or `neo4j+ssc`. Aliases use `neo4j+ssc`, which encrypts but does not verify the certificate:
fine between containers on one laptop, not for a shared deployment, which should use a certificate
from a CA the instances trust and `neo4j+s`.

Not in git. Make it once, then recreate the containers:

```bash
mkdir -p docker/tls/bolt/trusted docker/tls/bolt/revoked
openssl req -x509 -newkey rsa:2048 -nodes -days 825 -subj "/CN=qlsc-local" \
  -addext "subjectAltName=DNS:neo4j,DNS:qlsc-neo4j,DNS:neo4j-vg,DNS:qlsc-neo4j-vg,DNS:localhost,IP:127.0.0.1" \
  -keyout docker/tls/bolt/private.key -out docker/tls/bolt/public.crt
chmod 600 docker/tls/bolt/private.key
```
