#!/bin/sh
# nes-init entrypoint. Credentials arrive via env (NEO4J_USERNAME/NEO4J_PASSWORD
# are read natively by cypher-shell; TOOLS_PASSWORD comes from
# NES_TOOLS_PASSWORD in .env).
set -eu

shell() {
  cypher-shell -a neo4j://neo4j:7687 -d system \
    --param "toolsPassword => '${TOOLS_PASSWORD}'" "$@"
}

# 1. Idempotent provisioning.
shell -f /nes-setup.cypher

# 2. Converge tools_service on the current .env password, so rotation works.
#    22N89 = "new password same as old": the steady state, not an error.
if ! out=$(shell "ALTER USER tools_service SET PASSWORD \$toolsPassword SET PASSWORD CHANGE NOT REQUIRED;" 2>&1); then
  case "$out" in
    *22N89*) echo "tools_service password already current" ;;
    *) echo "$out" >&2; exit 1 ;;
  esac
fi
echo "nes-init complete"
