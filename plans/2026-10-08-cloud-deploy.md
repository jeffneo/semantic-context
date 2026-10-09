# Hosting the demo on GCP: a first deployment, one command up and one down

Status: in progress (2026-10-08). Steps 1 to 3 are built (below); the decisions at the end that are still open wait on you.

A colleague will show the demo at a conference, and installing it is the wrong ask. This plan puts the page, its live panels and the three Neo4j
instances on GCP in the pattern a customer would use: stateless parts on serverless, each database on its own small VM with its own disk, the
data a build artifact in Cloud Storage, no keys in the cloud, everything created and removed by Terraform.

## Revision, after the first hosted run (2026-10-08): no access code; the keys are the protection; one set of rules

The first hosted version gated its live panels behind a shared access code. That was a misreading of what was agreed ("a shared access code is okay, I can create a
dedicated one"): the dedicated thing meant is a set of **API keys made for this deployment, with spend and rate limits**, shared by every visitor, who enter nothing. The
page should open and run. This section supersedes the access code wherever the rest of this plan or the README mention it.

1. **No access code.** Out: `QLSC_DEMO_ACCESS_CODE`, the 401 path and the page's prompt (`CodeGate`), the secret `qlsc-demo-access-code`, `scripts/cloud access-code`.
2. **The keys.** The deployment holds a dedicated Anthropic key and a dedicated Azure OpenAI key, endpoint and version (embeddings), each with a limit set at the
   provider: a monthly spend cap, and a rate limit. They are in Secret Manager as the others are; you put their values in `deploy/gcp/.env` (untracked, not the
   checkout's root `.env`) and `scripts/cloud secrets` writes them. Cloud Run gets them as environment variables. The cache still answers every question the page offers, so
   the keys are the net under a miss (a state the cache does not cover), not what answers; a miss then works instead of failing, and costs at most what the cap allows.
3. **Presets only, everywhere.** One rule for the local page and the hosted one: the server runs only what the page offers (`ui/dist/presets.json`, written by
   `npm run presets`, which `scripts/stack up` runs), and the query and question boxes are read-only; a preset is chosen from the list. `QLSC_DEMO_HOSTED` is left meaning only
   "serve the page's files from here and answer your own origin". Nothing in the docs says a visitor edits a query.
4. **Capacity is not one-at-a-time, and the limit is not meant to be.** `METHODS_AT_ONCE = 2` in `server.py` is a laptop-sized limit carried over: each command is a
   process, and it *refuses* a third. Replaced by: a limit set by memory (a variable, 8 on Cloud Run's 4 GiB), a visitor who waits for a free slot instead of being refused,
   Cloud Run's concurrency set to match, and `demo_max_instances` 4. What is a real limit is Virtual Graph's heap (one machine, 5G, a 2g cap per transaction: the earlier
   out-of-memory under three concurrent runs was on 2G). That is measured with a load test of many concurrent visitors, and the machine is sized from the result.
5. **Housekeeping.** `debug_bolt_over_iap` off; the optional budget alert (`billing_account`); the README's cost line corrected (stopped machines still pay for their disks:
   about $30 a month, not a dollar; running, about $180).
6. **Memory.** The retention policy ([plans/2026-10-08-memory-retention.md](2026-10-08-memory-retention.md)) and a test customer per visitor, so concurrent visitors do not share
   a customer and what they leave expires.

Done in code (2026-10-08), not yet rolled out: 1, 3, 4's code, 2's wiring (the secrets, the environment, `scripts/cloud secrets` reading `deploy/gcp/.env`), 6 (the retention policy and `/api/pick`:
plans/2026-10-08-memory-retention.md). To roll out: `scripts/cloud up --image` (idempotent: it makes the new secrets first, fills them, builds and pushes the image, then applies).
Still to do: the load test of many concurrent visitors on the hosted service (it sizes Virtual Graph's machine), then the from-scratch rehearsal (`scripts/cloud destroy`, `up`).

## Lifecycle: the network outlives what runs on it (2026-10-08)

The first from-scratch rehearsal could not delete the subnet: Cloud Run's Direct VPC egress reserves a /28 in it per service (`serverless-ipv4-…`, purpose SERVERLESS), and Google released
none of them in over an hour after the service was deleted. A subnet cannot be deleted while one is in it, so a `destroy` that removes the network cannot finish, and a name
fixed in the code (`qlsc-demo`, `qlsc-demo-<region>`) cannot be reused until it does. Decided: the network, its subnet and the APIs are the long-lived part (they cost nothing); what runs
is `module.runtime` (the machines, their addresses, NAT, the firewall, the service, the sweep job, the registry, the bucket, the secrets, the budget). `scripts/cloud destroy` removes
the module and leaves the network; `destroy --everything` removes it too and waits for the release; `up` reuses the network. The subnet is a /22 so that reservations left behind do
not use it up. One state, a module boundary and `moved` blocks (no state surgery); the module can be promoted to a stack of its own if the two ever need separate owners.
Verified read-only before it was applied: the refactor plan moves every resource, rebuilds none, and a runtime destroy is 33 resources and none of the root's.
The first `up` after the change does one full apply (which moves the state); a targeted operation refuses to run until then.

## The shape

```
 visitor ──https──▶ Cloud Run `qlsc-demo`  (the page's static files and server.py: one container, one URL)
                         │  private network (Direct VPC egress)
        ┌────────────────┼──────────────────────┐
        ▼                ▼                      ▼
   db-semantic       db-memory              db-vg   (Virtual Graph; the composite `fennmoor`)
   neo4j, `bigquery` neo4j, `memory`        neo4j-vg ──▶ BigQuery
   8 GB, 100 GB disk 8 GB, 100 GB disk      8 GB, 100 GB disk
        ▲                ▲                      │ the composite reaches both through remote aliases
        └────────────────┴──────────────────────┘
 Cloud Storage: database dumps, Terraform state      Secret Manager: keys      Artifact Registry: the image
```

- **Semantic and memory on separate instances.** Today both are databases on one Neo4j (`estate.yaml`: `neo4j`, `memory.database`), and the composite `fennmoor`
  on the Virtual Graph instance reaches them through one remote alias. On GCP each gets its own VM and its own alias: the composite is where the three
  meet, which is the deployment pattern worth learning. Bolt TLS is already optional on every instance (`docker/tls`); the aliases use `neo4j+ssc`.
- **Disks.** At least 100 GB each, for the IO a bigger disk gets. `pd-balanced`; a Terraform variable.
- **Sizes.** All three 8 GB (e2-standard-2); `db-vg` was 4 GB, raised after the heap warning below. Heaps follow the machines (a variable each), not the 4G and 5G the
  laptop's compose uses. Virtual Graph ran out of heap at 2G under three concurrent runs (compose comment, 2026-09-27), which is why it is not 4 GB; the laptop's
  5G heap and 2g transaction cap fit 8 GB. `server.py`'s two-at-a-time limit (`METHODS_AT_ONCE`) holds per Cloud Run instance, so the instance cap is also the cap on
  what reaches Virtual Graph.
- **Cloud Run.** One service: a multi-stage image (Node builds `ui/dist`, Python serves it and `/api`). Scales to zero. Max instances low (2 to start).
  `server.py` changes: bind `0.0.0.0` and `$PORT`, serve `dist/` with the page's route fallback, allow its own origin (today only localhost), read
  database addresses from configuration. The query and command limits it already has stay.
- **No keys.** The VMs and Cloud Run run as attached service accounts (the estate's data-source identity, `qlsc`, to start; a variable). Nothing in the
  cloud holds a credentials file. Principals are still impersonated for real (`serviceAccountTokenCreator`), so the security chapter works as it does now.
  Locally the Virtual Graph container already runs as that service account through an impersonation file (`docker/nvg/README.md`); the cloud's
  difference is only that the credential is the machine's, so the compose file used on the VM has no credentials mount and no
  `GOOGLE_APPLICATION_CREDENTIALS`. Whether the pass-through jar picks up ambient credentials is the first thing to test.

## What the live panels call

Measured on 2026-10-08 with invalid keys, so a miss fails and costs nothing:

- `ask` embeds the question with Azure OpenAI (`emb_cache.json`) **before** anything else, and generates SQL or Cypher with Anthropic (`llm_cache/`). The
  hosted deployment needs both keys, not one.
- The four preset questions: the embeddings and the SQL route are cached; the Cypher route is cached only for the agents question. The page's presets use
  route `auto`, which picks the cached one, so they should answer from cache **if the caches ship in the image**. Not tested: the same questions as a named
  principal, and the cache after a day change (one prompt, `precedent`, includes today's date).
- A question typed freely, or a route changed by hand, is a miss: two paid calls. `recall`, `remember`, the Cypher and SQL tabs and the other commands call no model.
- Measured again for the whole page (`generate/hosted_work.py`, every `ask` preset as every principal, keys invalid): **5 of 60** answered from cache. The
  cache is per principal, and the router-trace questions were never run through `ask`. So the cache is warmed once with real keys (`--warm`, about 3 cents a
  question, about $2 in all) and shipped: that is a step, not a given.

Decided: **the hosted page runs its presets only.** The server enforces it (`QLSC_DEMO_HOSTED=1`: `ui/dist/presets.json`, written by `npm run build` from the page's
own presets, is the whole list of Cypher, SQL, questions and recalls it will run), and the page shows the query and question boxes read-only. So the guards: the
presets only; the warmed caches in the image; a shared access code gates `/api` (the page itself is public); Cloud Run max instances; new keys made for this
deployment, with spend limits, kept apart from the ones used locally; a budget alert on the project.

## Secrets and configuration

- No `.env` in the cloud. Keys live in Secret Manager and reach Cloud Run as environment variables.
- Locally, the hosted deployment has its own untracked file, `deploy/gcp/.env` (gitignored), never the repository's root `.env`. `scripts/cloud secrets`
  reads it and writes secret versions with `gcloud`; Terraform creates only the empty secrets, because a secret passed to Terraform is written into its
  state in the clear.
- Project, region and the service account names go in `deploy/gcp/terraform.tfvars` (gitignored), with an example file committed.
- The Neo4j license agreement: `NEO4J_ACCEPT_LICENSE_AGREEMENT: ${NEO4J_ACCEPT_LICENSE_AGREEMENT:-eval}` in `docker-compose.yml`, so a clone gets `eval` and a
  non-evaluation license is set only in an untracked `.env` or `terraform.tfvars`. The Enterprise Studio license file is already referenced, never committed.
- Terraform state: a versioned Cloud Storage bucket, created by a bootstrap step in `scripts/cloud`.
- Terraform runs as your default gcloud user (not the `qlsc` service account, which only reads data), with the project passed explicitly; your gcloud
  configurations are not changed.

## Data

A dump of just what the demo reads: the `bigquery` database (semantic layer), the `memory` database, and the Virtual Graph model (`work/virtual/`). Made
by `scripts/cloud dump` (an export of the databases the page reads, not the 4.7 GB pipeline volume), written to the bucket, restored by each VM at boot. A VM is
disposable: destroy it, apply again, and it comes back as it was dumped. The process database is not in the page yet, so it is not in the dump.

## Repository layout

- `deploy/gcp/terraform/`: network, the three VMs, Cloud Run, Artifact Registry, buckets, secrets, IAM, the budget alert.
- `deploy/gcp/vm/`: the compose files and the boot script the VMs run (restore, start, create the aliases and the composite).
- `deploy/gcp/README.md`: how to bring it up, and what each part is for.
- `docker/demo/Dockerfile`: the page and server image, next to `docker/nes` and `docker/nvg`.
- `scripts/cloud`: `up`, `down` (stops the VMs and scales Cloud Run to zero: pennies a day), `destroy` (removes everything; the dumps stay), `status`, `secrets`,
  `dump`. Beside `scripts/stack`, which stays the laptop's command.

## Steps

1. The license variable in `docker-compose.yml`.
2. The demo image and `server.py`'s changes; run it locally in compose against the local instances (proves the image).
3. `memory` gets its own address in the configuration, apart from the semantic layer's (today they share `neo4j`), so the two can be on different hosts.
   The composite is rebuilt with two aliases. A refactor that must not change results: the memory evaluation and the fingerprint run around it.
4. Test the Virtual Graph on ambient credentials, locally first (a container with a service account's token from the metadata server cannot be had
   locally, so this step is done on the first VM).
5. The data dump and restore.
6. Terraform and the VM boot scripts; first `up` in the project.
7. The access code (server and page), the budget alert, a load test at two simultaneous visitors.
8. A rehearsal from a clean `up` to a working page, and `down`, `up` again, `destroy`.

## Built so far (steps 1 to 3, and the part of 2 that the image needs)

- `NEO4J_ACCEPT_LICENSE_AGREEMENT` is `${...:-eval}` in `docker-compose.yml`; `.env.example` names it.
- `memory.neo4j` (`defaults.yaml`) gives memory an instance of its own; `memory.memory_instance` and `memory_graph` use it; `server.py` and the UI generators too. Empty,
  as it is everywhere today, it is the semantic layer's instance. `tests/test_config.py`.
- `QLSC_OVERRIDES` (`config.py`): a second settings file merged over the estate's, so a deployment says where its databases are without editing the estate's file.
- `warehouse.identity: ambient` (`warehouse/bigquery.py`): the connector signs in as the service account the machine runs as (`google.auth.default`), not through `gcloud`
  (which a container does not have), and impersonates the principals from it as before. `gcloud` stays the default. The process corpus's reader (`warehouse/gcs.py`)
  still needs gcloud; the hosted demo does not use it.
- `server.py`: `QLSC_DEMO_HOSTED`, `QLSC_DEMO_HOST`, `$PORT`, `QLSC_DEMO_STATIC`; serves `ui/dist`, answers its own origin, `/healthz`, presets only (`tests/test_demo_server.py`).
- `ui/scripts/presets.ts` (`npm run presets`, part of `npm run build`), and the read-only boxes (`live/LiveRun.tsx`).
- `generate/hosted_work.py`: the slice of `work/` the presets read, never the signing key.
- `docker/demo/`: the image, its ignore list, the overrides file for compose; `docker compose --profile demo` runs it beside the local stack.

## Step 4, done (2026-10-08): Virtual Graph on a machine's own identity

`db-vg` (e2-standard-2, 8 GB, 100 GB disk, no public address, `qlsc-bq` attached) runs the Virtual Graph with **no credentials file**: the datasource's
`OAuthType=3` finds the machine's service account through the metadata server, and the pass-through impersonates each principal from it. The page's `rows` presets,
signed and sent through an IAP tunnel, gave the same result as the laptop's Virtual Graph for every principal: admin and risk read, marketing and contact-center are
refused by BigQuery on the tables they may not see. `secret.json` still names `/nvg_home/credentials.json`; an empty file satisfies it (as it does locally, where
compose mounts the credentials over an empty one). Two things found: the image's entrypoint `chown`s the jars, so they cannot be mounted read-only; and Neo4j
takes a few minutes to answer after the container starts, so "failed to connect to backend" through IAP is not a firewall problem for the first five.

## Step 5, done (2026-10-08): the data, three machines, the composite

`scripts/cloud dump` takes an online backup of the layer's and memory's databases from the local container (they stay up) and puts it in the bucket under a
timestamp, with `dump/LATEST` naming it; nothing is overwritten or deleted. `db-semantic` and `db-memory` restore from it at first boot (the node counts match the
laptop's: 9,735 and 129,695; all indexes online), each with a self-signed bolt certificate; `db-vg` makes the keystore and the composite `fennmoor`, whose aliases
point at the other two (`neo4j+ssc`) and at its own virtual graph. The page's composite query, run through an IAP tunnel, gave the laptop's rows: the layer from one
machine, live BigQuery rows through Virtual Graph, three rows, 3,005 closure calls at Tulsa. Each machine has a reserved internal address. Found on the way: Neo4j
refuses a restore path at the filesystem root; the `system` database accepts no `RETURN 1`, so a readiness check uses `SHOW DATABASES`; the provider rejects a plan
whose startup script changes while an apply runs; `debian-12` is a family, so existing machines ignore a newer image (a rebuild is `-replace`).
Open: the very first boot of `db-vg` reported "did not answer" for eleven minutes though Neo4j had started, and the same script succeeded when re-run. It is not
explained; `wait_bolt` now logs what it saw, and the from-scratch rehearsal (step 8) is where it shows again or not.

## What does not change

The pipeline, the model, the results, and the laptop's `scripts/stack`.

## Open decisions (yours)

1. **Retention of what memory keeps.** There is none: no TTL and no retention policy. A fact has `holds_until` (when it is stale), but a stale node stays for
   ever, and conversations, steps and decisions (the audit record) are kept by design. Two different things, I would say: the _fetched rows_ are copies that
   have left the warehouse's row policies, so they want a retention limit; the _audit record_ is the point of the memory database, so it wants a stated policy
   (keep, by default) and a way to archive. I'd write that as its own plan (it changes the model and the method), with a limit for fetched facts in
   `defaults.yaml` and a sweep command. The hosted demo then sets a short one. It is not required for the first hosted version.
2. **The hosted memory panel.** Restore memory from the dump at each boot, and add a per-visitor default customer: the panel picks one not yet in memory and
   forgets contexts older than a few minutes (the same retention mechanism with a short setting; `forget.py` is the one-customer piece, no preflight needed).
3. ~~Free-text questions~~: decided, presets only.
4. ~~The Virtual Graph machine at 4 GB~~: decided, 8 GB.
5. **Your default gcloud login.** `gcloud projects describe` returned UNAUTHENTICATED (`ACCESS_TOKEN_TYPE_UNSUPPORTED`) with the default configuration today, so it
   probably needs `gcloud auth login` from your own terminal before step 6. Nothing was changed.
