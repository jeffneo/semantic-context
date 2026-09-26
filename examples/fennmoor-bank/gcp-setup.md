# Connecting the spec to BigQuery

What BigQuery is used for: **validation, not data.** The build creates the
Fennmoor estate as *empty* tables and views, then dry-runs every model's SQL
in dependency order. BigQuery's own parser and type checker then confirm that
all 197 derived tables and views are valid BigQuery and that each output schema
matches the spec. Later, the query-log generator uses the same dry runs to
reject any generated query that isn't valid BigQuery SQL.

Cost: effectively zero. Empty tables store nothing, and dry runs are never
billed. The only billed operation would be an accidental real query against
empty tables; the quota in step 6 caps even that.

## Setup (about 5 minutes, run by you)

Everything below leaves your default gcloud configuration and default project
untouched. qlsc and the generators get a **service account they impersonate with
your login** - no key file is ever created.

### 1. Choose the project

A dedicated project is best. A shared project works too: every dataset the
deploy creates gets a prefix (default `fnb_`), so it cannot collide with
anything already there.

```bash
export QLSC_PROJECT=your-project-id
```

### 2. Enable the BigQuery API

```bash
gcloud services enable bigquery.googleapis.com --project=$QLSC_PROJECT
```

### 3. Create the service account

```bash
gcloud iam service-accounts create qlsc-bq --display-name="Query-log semantic context" --project=$QLSC_PROJECT
```

### 4. Grant it one role: BigQuery User

`roles/bigquery.user` can create datasets and run jobs, and it becomes owner of
**only the datasets it creates**. It cannot read data in datasets that
already exist in the project.

```bash
gcloud projects add-iam-policy-binding $QLSC_PROJECT --member="serviceAccount:qlsc-bq@$QLSC_PROJECT.iam.gserviceaccount.com" --role="roles/bigquery.user" --condition=None
```

### 5. Let your account impersonate it

```bash
gcloud iam service-accounts add-iam-policy-binding qlsc-bq@$QLSC_PROJECT.iam.gserviceaccount.com --member="user:you@example.com" --role="roles/iam.serviceAccountTokenCreator" --project=$QLSC_PROJECT
```

### 6. Cap query bytes (belt and braces)

Console -> IAM & Admin -> Quotas -> filter "BigQuery API" -> **Query usage per
day** -> set to 10 GiB for this project. Dry runs and DDL don't count against
it; it only stops a mistake.

### 7. Create a separate gcloud configuration

A named configuration, not your default one. qlsc selects it explicitly (the
config's `warehouse.gcloud_config`), as does `CLOUDSDK_ACTIVE_CONFIG_NAME=qlsc`
on the command line.

```bash
gcloud config configurations create qlsc --no-activate
```

```bash
gcloud config set project $QLSC_PROJECT --configuration=qlsc
```

```bash
gcloud config set account you@example.com --configuration=qlsc
```

```bash
gcloud config set auth/impersonate_service_account qlsc-bq@$QLSC_PROJECT.iam.gserviceaccount.com --configuration=qlsc
```

The `create` command may leave `qlsc` active. Switch back to your default:

```bash
gcloud config configurations activate default
```

### 8. Verify

```bash
CLOUDSDK_ACTIVE_CONFIG_NAME=qlsc bq ls --project_id=$QLSC_PROJECT
```

An empty listing (or your existing datasets, if shared) means it works. Put
the project id in `estate.yaml` (`warehouse.project`).

## What the generators do with it (`generate/deploy.py`)

1. Create 43 datasets named `fnb_<dataset>` in US multi-region.
2. Create the 104 raw tables empty, from `build/ddl/`. Sharded tables (GA4
   daily, Avaya monthly) get a representative subset of shards unless you
   want all 849.
3. Create the 93 staging views. View creation itself validates their SQL.
4. For each downstream model in dependency order: dry-run its SELECT, compare
   the returned schema to the spec, then create it as an empty table.
5. Report every failure against the spec file and line it came from.

The logical project ids in the spec (`fennmoor-raw`, `fennmoor-dw`,
`fennmoor-analytics`) are rewritten to your project at deploy time only. The
generated query log keeps the logical ids, so it reads like a real
three-project estate.

## Undoing it

Everything lives in `fnb_*` datasets owned by the service account:

```bash
CLOUDSDK_ACTIVE_CONFIG_NAME=qlsc bq ls --project_id=$QLSC_PROJECT
```

Deleting them, the service account and the `qlsc` configuration removes all
trace.
