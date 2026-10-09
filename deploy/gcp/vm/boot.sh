#!/bin/bash
# What every database machine runs at boot (Terraform puts it in the instance's `startup-script`; it reads what is its own from the instance's metadata).
# It is safe to run again, and runs at every start: it makes the same container from the same inputs, and restores the data only into an empty machine.
# Its output is in the serial console:  gcloud compute instances get-serial-port-output db-<role> --zone <zone>
#
# Roles (metadata `role`): `semantic` and `memory` each run one database of a Neo4j instance, restored from the dump in the bucket (scripts/cloud dump);
# `vg` runs Virtual Graph and the composite `fennmoor` that reaches the other two (and its own virtual graph) through remote aliases.
set -euo pipefail

meta() { curl -fsS -H 'Metadata-Flavor: Google' "http://metadata.google.internal/computeMetadata/v1/instance/attributes/$1"; }
say() { echo "qlsc-boot: $*"; }

ROLE=$(meta role); BUCKET=$(meta bucket); HEAP=$(meta heap); IMAGE=$(meta image); LICENSE=$(meta license)
HOME_DIR=/opt/qlsc
NEO4J_UID=7474 # the image's neo4j user
mkdir -p "$HOME_DIR"

if ! command -v docker >/dev/null; then
  say "installing docker"
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq docker.io
fi
systemctl enable --now docker

# Google's CLI, as a container: it signs in as the machine's attached service account, and needs nothing installed.
CLOUDSDK=gcr.io/google.com/cloudsdktool/google-cloud-cli:slim
gcloudc() { docker run --rm -v "$HOME_DIR:$HOME_DIR" "$CLOUDSDK" gcloud "$@"; }
# A secret's latest value. A secret may not have one yet when the machine first boots (Terraform makes the secret, `scripts/cloud secrets` fills it): wait.
secret() {
  local i
  for i in $(seq 1 60); do
    gcloudc secrets versions access latest --secret="$1" 2>/dev/null && return 0
    sleep 15
  done
  say "no value for the secret $1" >&2
  return 1
}

PASSWORD=$(secret qlsc-demo-neo4j-password)

# A certificate of its own, self-signed: bolt is encrypted, and a remote alias (a composite reaches the other instances this way, and accepts only
# neo4j+s or neo4j+ssc) can connect. `+ssc` does not check who it is talking to; a CA both ends trust and `+s` is the next step (plans/2026-10-08-cloud-deploy.md).
tls() {
  local dir="$HOME_DIR/tls/bolt"
  if [ ! -f "$dir/private.key" ]; then
    mkdir -p "$dir/trusted" "$dir/revoked"
    openssl req -x509 -newkey rsa:2048 -nodes -days 825 -subj "/CN=$(hostname)" \
      -addext "subjectAltName=DNS:$(hostname),IP:$(hostname -I | awk '{print $1}')" \
      -keyout "$dir/private.key" -out "$dir/public.crt" 2>/dev/null
    chmod 600 "$dir/private.key"
  fi
  chown -R "$NEO4J_UID:$NEO4J_UID" "$HOME_DIR/tls"
}
TLS_ENV=(-e NEO4J_server_bolt_tls__level=OPTIONAL -e NEO4J_dbms_ssl_policy_bolt_enabled=true -e NEO4J_dbms_ssl_policy_bolt_base__directory=/ssl/bolt
         -e NEO4J_dbms_ssl_policy_bolt_client__auth=NONE)

wait_bolt() {
  local i out
  for i in $(seq 1 120); do
    out=$(docker exec "$1" cypher-shell -u neo4j -p "$PASSWORD" -d system "SHOW DATABASES" 2>&1) && return 0
    [ $((i % 6)) -eq 0 ] && say "waiting for $1 (attempt $i): ${out:0:160}"
    sleep 5
  done
  say "$1 did not answer: ${out:0:300}" >&2
  return 1
}

tls
mkdir -p "$HOME_DIR/data"

case "$ROLE" in
  semantic | memory)
    DB=$(meta database)
    if [ ! -f "$HOME_DIR/restored" ]; then
      say "restoring $DB from the dump"
      STAMP=$(gcloudc storage cat "gs://$BUCKET/dump/LATEST")
      rm -rf "$HOME_DIR/backups"; mkdir -p "$HOME_DIR/backups"
      gcloudc storage cp "gs://$BUCKET/dump/$STAMP/$DB/*" "$HOME_DIR/backups/"
      chown -R "$NEO4J_UID:$NEO4J_UID" "$HOME_DIR/data" "$HOME_DIR/backups"
      docker run --rm -e NEO4J_ACCEPT_LICENSE_AGREEMENT="$LICENSE" -v "$HOME_DIR/data:/data" -v "$HOME_DIR/backups:/qlsc/backups" "$IMAGE" \
        neo4j-admin database restore --from-path=/qlsc/backups --overwrite-destination=true "$DB"
      echo "$STAMP" > "$HOME_DIR/restored"
    fi
    chown -R "$NEO4J_UID:$NEO4J_UID" "$HOME_DIR/data"
    docker rm -f neo4j >/dev/null 2>&1 || true
    say "starting Neo4j ($IMAGE, heap $HEAP)"
    docker run -d --name neo4j --restart unless-stopped -p 7687:7687 \
      -e NEO4J_AUTH="neo4j/$PASSWORD" \
      -e NEO4J_ACCEPT_LICENSE_AGREEMENT="$LICENSE" \
      -e NEO4J_server_memory_heap_max__size="$HEAP" \
      -e NEO4J_server_memory_pagecache_size=2G \
      "${TLS_ENV[@]}" \
      -v "$HOME_DIR/data:/data" -v "$HOME_DIR/tls/bolt:/ssl/bolt" \
      "$IMAGE"
    wait_bolt neo4j
    # a restored database is files until the instance is told of it
    docker exec neo4j cypher-shell -u neo4j -p "$PASSWORD" -d system "CREATE DATABASE \`$DB\` IF NOT EXISTS WAIT"
    ;;

  vg)
    # Virtual Graph: its model (datasource, schema, views) and the two jars from the bucket, the signing key from the secret store. No credentials file: the
    # datasource asks the driver for application-default credentials (OAuthType 3), which on this machine are its service account's.
    SEMANTIC=$(meta semantic_host); MEMORY=$(meta memory_host)
    say "fetching the Virtual Graph's model and jars"
    rm -rf "$HOME_DIR/nvg_home" "$HOME_DIR/lib"
    mkdir -p "$HOME_DIR/nvg_home" "$HOME_DIR/lib"
    gcloudc storage cp -r "gs://$BUCKET/vg/virtual/*" "$HOME_DIR/nvg_home/"
    gcloudc storage cp "gs://$BUCKET/vg/lib/*.jar" "$HOME_DIR/lib/"
    secret qlsc-demo-passthrough-key > "$HOME_DIR/nvg_home/passthrough.key"
    chmod 600 "$HOME_DIR/nvg_home/passthrough.key"
    : > "$HOME_DIR/nvg_home/credentials.json" # secret.json names this file; empty, as on a workstation, where compose mounts the credentials over it. The driver uses the machine's own.
    # The keystore holds the passwords of the composite's remote aliases (Neo4j encrypts them with its key).
    KEYSTORE_PASSWORD=$(secret qlsc-demo-keystore-password)
    if [ ! -f "$HOME_DIR/keystore/neo4j.keystore" ]; then
      mkdir -p "$HOME_DIR/keystore"
      docker run --rm --entrypoint keytool -v "$HOME_DIR/keystore:/keystore" "$IMAGE" -genseckey -keyalg aes -keysize 256 \
        -storetype pkcs12 -keystore /keystore/neo4j.keystore -alias neo4j -storepass "$KEYSTORE_PASSWORD"
    fi
    chown -R "$NEO4J_UID:$NEO4J_UID" "$HOME_DIR/nvg_home" "$HOME_DIR/data" "$HOME_DIR/keystore"
    docker rm -f neo4j-vg >/dev/null 2>&1 || true
    say "starting Virtual Graph ($IMAGE, heap $HEAP)"
    docker run -d --name neo4j-vg --restart unless-stopped -p 7687:7687 \
      -e NEO4J_AUTH="neo4j/$PASSWORD" \
      -e NEO4J_ACCEPT_LICENSE_AGREEMENT="$LICENSE" \
      -e NEO4J_internal_virtual__graph_enabled=true \
      -e NEO4J_internal_virtual__graph_home=/nvg_home \
      -e NEO4J_server_memory_heap_max__size="$HEAP" \
      -e NEO4J_server_memory_pagecache_size=512M \
      -e NEO4J_db_memory_transaction_max=2g \
      -e NEO4J_dbms_memory_transaction_total_max=3g \
      -e NEO4J_db_transaction_timeout=180s \
      -e NEO4J_dbms_security_keystore_path=/keystore/neo4j.keystore \
      -e NEO4J_dbms_security_keystore_password="$KEYSTORE_PASSWORD" \
      -e NEO4J_dbms_security_key_name=neo4j \
      "${TLS_ENV[@]}" \
      -v "$HOME_DIR/nvg_home:/nvg_home" \
      -v "$HOME_DIR/keystore:/keystore" \
      -v "$HOME_DIR/data:/data" -v "$HOME_DIR/tls/bolt:/ssl/bolt" \
      -v "$HOME_DIR/lib/qlsc-vg-passthrough.jar:/var/lib/neo4j/lib/google-cloud-bigquery-jdbc-1.0.0-all.jar" \
      -v "$HOME_DIR/lib/google-cloud-bigquery-jdbc-1.0.0-all.jar:/var/lib/neo4j/qlsc/google-cloud-bigquery-jdbc-1.0.0-all.jar" \
      "$IMAGE"
    wait_bolt neo4j-vg
    # The composite: the semantic layer and memory, each on its own machine, and the virtual graph here: one query over all three.
    say "making the composite fennmoor (semantic $SEMANTIC, memory $MEMORY)"
    docker exec -i neo4j-vg cypher-shell -u neo4j -p "$PASSWORD" -d system --param "pw => '$PASSWORD'" <<CYPHER
CREATE COMPOSITE DATABASE fennmoor IF NOT EXISTS;
CREATE OR REPLACE ALIAS fennmoor.semantic FOR DATABASE bigquery AT 'neo4j+ssc://$SEMANTIC:7687' USER neo4j PASSWORD \$pw;
CREATE OR REPLACE ALIAS fennmoor.memory FOR DATABASE memory AT 'neo4j+ssc://$MEMORY:7687' USER neo4j PASSWORD \$pw;
CREATE OR REPLACE ALIAS fennmoor.rows FOR DATABASE neo4j AT 'neo4j+ssc://localhost:7687' USER neo4j PASSWORD \$pw;
CYPHER
    ;;

  *)
    say "role $ROLE is not known"
    exit 1
    ;;
esac
say "done"
