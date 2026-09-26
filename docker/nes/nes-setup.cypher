// Neo4j Enterprise Studio prerequisites - runs against the `system` database.
// https://neo4j.com/docs/enterprise-studio/current/prerequisites/
//
// Applied once by the `nes-init` service before Studio starts. Idempotent, so
// re-running after a `make nes` is harmless.
//
// The service-account password is NOT stored here. It arrives as the
// $toolsPassword parameter, sourced from NES_TOOLS_PASSWORD in .env, and the
// same variable configures the enterprise-studio service - so the two sides
// cannot drift. Studio fails to start with an opaque asset-store error if they
// do, which is why this is a parameter and not a literal in two files.

// 1. Service account owning the tool asset database.
CREATE USER tools_service IF NOT EXISTS
  SET PASSWORD $toolsPassword
  SET PASSWORD CHANGE NOT REQUIRED;

// IF NOT EXISTS leaves an existing user's password alone. Rotation is handled
// by docker/nes/nes-init.sh, which runs an ALTER after this script - it can't live
// here because Neo4j rejects setting a password to its current value (22N89),
// which would fail every run after the first.

// `architect` carries the token and constraint privileges Studio needs to build
// its asset schema on first start.
GRANT ROLE architect TO tools_service;

// 2. The asset database must exist before Studio boots. Name must match
//    NES_assetStore_default_database in docker-compose.yml.
CREATE DATABASE `tools-storage` IF NOT EXISTS;

// 3. Privileges on the deployments users actually query. Without these, Bloom
//    silently shows no schema (it reads SHOW INDEXES / SHOW CONSTRAINTS) and
//    asset sharing cannot enumerate roles or users to share with.
GRANT SHOW CONSTRAINTS ON DATABASES * TO reader;
GRANT SHOW INDEXES ON DATABASES * TO reader;
GRANT SHOW ROLE ON DBMS TO reader;
GRANT SHOW USER ON DBMS TO reader;
