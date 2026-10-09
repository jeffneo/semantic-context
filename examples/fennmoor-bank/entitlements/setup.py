"""The entitlements the example's test principals stand for, set up in BigQuery (plans/2026-09-27-entitlements.md).

Three service accounts stand in for people; the gateway (`qlsc ask --as`) impersonates them:
  - qlsc-marketing: marketing and core customer data, no identifier columns
  - qlsc-risk: fraud, lending and core data, with identifiers; customers in two states only
  - qlsc-contact-center: contact-center data only
Each gets BigQuery job rights on the project, read on its datasets and on the virtual graph's views
(which read the same tables, so BigQuery still decides), and the estate's connector identity (qlsc-bq)
may mint tokens for it. The identifier columns get one policy tag, readable by the risk principal and
the estate's existing readers; `dim_customer` gets a row access policy (two states for risk, every row
for the existing readers and marketing: a row policy hides every row from anyone it doesn't name).

Runs as an administrator, because granting IAM roles, policy tags and row policies needs rights the estate's runtime identity
(qlsc-bq) must not have. The administrator is a gcloud configuration of its own, named in QLSC_ADMIN_GCLOUD_CONFIG: logged in as
a person who owns the project, with no service account impersonated (see gcp-setup.md). That person's account is read from the
configuration at run time and is never written in this file. If the configuration is missing, or impersonates a service account,
the calls fail on permissions. Prints what it would do; --apply does it; each step is skipped when it is already in place, so it
can be rerun, and must be after a fill recreates a tagged table. Nothing here deletes anything.

Usage: QLSC_ADMIN_GCLOUD_CONFIG=<config> uv run examples/fennmoor-bank/entitlements/setup.py [--apply]
"""

from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
import time
from pathlib import Path

import google.auth.credentials
from google.auth.transport.requests import AuthorizedSession
from google.cloud import bigquery

from qlsc import config

# the project is the estate's (QLSC_GCP_PROJECT in .env replaces its placeholder): no committed file names it
PROJECT = config.load(Path(__file__).resolve().parents[1] / "estate.yaml")["warehouse"]["project"]
LOCATION = "us"
ADMIN_CONFIG = os.environ.get("QLSC_ADMIN_GCLOUD_CONFIG")
if not ADMIN_CONFIG:
    raise SystemExit(
        "set QLSC_ADMIN_GCLOUD_CONFIG to the gcloud configuration of the project's administrator (gcp-setup.md): "
        "this script grants IAM roles, which the estate's identity may not"
    )


def admin_account() -> str:
    """The administrator's account, from their gcloud configuration."""
    env = {**os.environ, "CLOUDSDK_ACTIVE_CONFIG_NAME": ADMIN_CONFIG}
    out = subprocess.run(
        ["gcloud", "config", "get-value", "account"], env=env, capture_output=True, text=True
    )
    account = out.stdout.strip()
    if out.returncode or not account or account == "(unset)":
        raise SystemExit(f"the gcloud configuration {ADMIN_CONFIG!r} has no account: log in under it")
    return f"user:{account}"


OWNER = admin_account()
ESTATE = f"qlsc-bq@{PROJECT}.iam.gserviceaccount.com"  # the connector's and Virtual Graph's identity
APIS = ["iam.googleapis.com", "iamcredentials.googleapis.com", "datacatalog.googleapis.com"]
GRAPH = "fnb_graph"  # the virtual graph's views
PRINCIPALS = {
    "qlsc-marketing": ["fnb_dw_marketing", "fnb_dw_core", "fnb_dw_customer"],
    "qlsc-risk": ["fnb_dw_risk", "fnb_fraud_platform", "fnb_loan_origination", "fnb_dw_core"],
    "qlsc-contact-center": ["fnb_dw_contact_center", "fnb_genesys_cloud", "fnb_contact_center_legacy"],
}
IDENTIFIERS = {
    "fnb_dw_core.dim_customer": [
        "cif_number",
        "full_name",
        "birth_date",
        "tax_id_hash",
        "primary_email",
        "primary_mobile",
    ],
    "fnb_dw_core.dim_account": ["primary_cif_number"],
    "fnb_dw_customer.customer_360": ["cif_number", "full_name", "primary_email"],
}
TAXONOMY, TAG = "qlsc-identifiers", "identifier"
ROWS_TABLE = "fnb_dw_core.dim_customer"
RISK_STATES = ["KS", "NE"]
CATALOG = "https://datacatalog.googleapis.com/v1"
USAGE = f"https://serviceusage.googleapis.com/v1/projects/{PROJECT}/services"
IAM = f"https://iam.googleapis.com/v1/projects/{PROJECT}/serviceAccounts"
CRM = f"https://cloudresourcemanager.googleapis.com/v1/projects/{PROJECT}"


def sa(name: str) -> str:
    return f"{name}@{PROJECT}.iam.gserviceaccount.com"


TAG_READERS = [OWNER, f"serviceAccount:{ESTATE}", f"serviceAccount:{sa('qlsc-risk')}"]
ALL_ROWS = [OWNER, f"serviceAccount:{ESTATE}", f"serviceAccount:{sa('qlsc-marketing')}"]


class OwnerCredentials(google.auth.credentials.Credentials):
    """A token from the administrator's gcloud configuration, as that configuration is set (nothing is switched off here)."""

    def refresh(self, request):
        env = {**os.environ, "CLOUDSDK_ACTIVE_CONFIG_NAME": ADMIN_CONFIG}
        out = subprocess.run(
            ["gcloud", "auth", "print-access-token"], env=env, capture_output=True, text=True, check=True
        )
        self.token = out.stdout.strip()
        self.expiry = dt.datetime.now(dt.UTC).replace(tzinfo=None) + dt.timedelta(minutes=45)


CREDS = OwnerCredentials()
HTTP = AuthorizedSession(CREDS)
BQ = bigquery.Client(project=PROJECT, credentials=CREDS, location="US")


def call(method: str, url: str, body: dict | None = None) -> dict:
    r = HTTP.request(method, url, json=body)
    if r.status_code != 200:
        raise SystemExit(f"{method} {url}: {r.status_code} {r.text[:400]}")
    return r.json() if r.text else {}


def step(apply: bool, done: bool, what: str, do=None) -> None:
    print(f"  {'ok  ' if done else 'DO  ' if apply else 'plan'} {what}", flush=True)
    if apply and not done and do:
        do()


def add_binding(get_url: str, set_url: str, role: str, member: str) -> None:
    """Read-modify-write of an IAM policy, with its etag: one member added to one role."""
    p = call("POST", get_url, {})
    for b in p.setdefault("bindings", []):
        if b["role"] == role:
            b["members"].append(member)
            break
    else:
        p["bindings"].append({"role": role, "members": [member]})
    call("POST", set_url, {"policy": p})


def has_binding(policy: dict, role: str, member: str) -> bool:
    return any(b["role"] == role and member in b["members"] for b in policy.get("bindings", []))


def api_on(api: str) -> bool:
    return call("GET", f"{USAGE}/{api}").get("state") == "ENABLED"


def apis(apply: bool) -> None:
    for api in APIS:

        def enable(api=api):
            op = call("POST", f"{USAGE}/{api}:enable", {})
            for _ in range(60):
                if op.get("done"):
                    return
                time.sleep(5)
                op = call("GET", f"https://serviceusage.googleapis.com/v1/{op['name']}")
            raise SystemExit(f"timed out enabling {api}")

        step(apply, api_on(api), f"enable {api}", enable)


def accounts(apply: bool) -> None:
    have = (
        {a["email"] for a in call("GET", IAM).get("accounts", [])} if api_on("iam.googleapis.com") else set()
    )
    for name in PRINCIPALS:
        body = {"accountId": name, "serviceAccount": {"displayName": f"{name} (qlsc test principal)"}}
        step(
            apply,
            sa(name) in have,
            f"create service account {sa(name)}",
            lambda body=body: call("POST", IAM, body),
        )
    role, member = "roles/iam.serviceAccountTokenCreator", f"serviceAccount:{ESTATE}"
    for name in PRINCIPALS:  # the estate's connector acts for each principal: it mints their tokens
        url = f"{IAM}/{sa(name)}"
        done = sa(name) in have and has_binding(call("POST", f"{url}:getIamPolicy", {}), role, member)
        step(
            apply,
            done,
            f"{ESTATE} may impersonate {sa(name)}",
            lambda url=url: add_binding(f"{url}:getIamPolicy", f"{url}:setIamPolicy", role, member),
        )


def project_roles(apply: bool) -> None:
    policy, role = call("POST", f"{CRM}:getIamPolicy", {}), "roles/bigquery.jobUser"
    for name in PRINCIPALS:
        member = f"serviceAccount:{sa(name)}"
        step(
            apply,
            has_binding(policy, role, member),
            f"{role} on the project for {sa(name)}",
            lambda member=member: add_binding(f"{CRM}:getIamPolicy", f"{CRM}:setIamPolicy", role, member),
        )


def datasets(apply: bool) -> None:
    for name, sets in PRINCIPALS.items():
        for ds in [*sets, GRAPH]:
            d = BQ.get_dataset(f"{PROJECT}.{ds}")
            done = any(e.entity_id == sa(name) and e.role == "READER" for e in d.access_entries)

            def grant(d=d, name=name):
                d.access_entries = [
                    *d.access_entries,
                    bigquery.AccessEntry("READER", "userByEmail", sa(name)),
                ]
                BQ.update_dataset(d, ["access_entries"])

            step(apply, done, f"read {ds} for {sa(name)}", grant)


def find(url: str, key: str, display: str) -> dict | None:
    return next((x for x in call("GET", url).get(key, []) if x["displayName"] == display), None)


def policy_tag(apply: bool) -> str | None:
    taxonomies = f"{CATALOG}/projects/{PROJECT}/locations/{LOCATION}/taxonomies"
    on = api_on("datacatalog.googleapis.com")
    tax = find(taxonomies, "taxonomies", TAXONOMY) if on else None
    body = {"displayName": TAXONOMY, "activatedPolicyTypes": ["FINE_GRAINED_ACCESS_CONTROL"]}
    step(
        apply,
        tax is not None,
        f"taxonomy {TAXONOMY} ({LOCATION}), fine-grained access control",
        lambda: call("POST", taxonomies, body),
    )
    if apply and tax is None:
        tax = find(taxonomies, "taxonomies", TAXONOMY)
    tag = find(f"{CATALOG}/{tax['name']}/policyTags", "policyTags", TAG) if tax else None
    step(
        apply,
        tag is not None,
        f"policy tag {TAG}",
        lambda: call("POST", f"{CATALOG}/{tax['name']}/policyTags", {"displayName": TAG}),
    )
    if apply and tag is None:
        tag = find(f"{CATALOG}/{tax['name']}/policyTags", "policyTags", TAG)
    role = "roles/datacatalog.categoryFineGrainedReader"
    policy = call("POST", f"{CATALOG}/{tag['name']}:getIamPolicy", {}) if tag else {}
    for m in TAG_READERS:
        step(
            apply,
            has_binding(policy, role, m),
            f"fine-grained read of {TAG} for {m}",
            lambda m=m: add_binding(
                f"{CATALOG}/{tag['name']}:getIamPolicy", f"{CATALOG}/{tag['name']}:setIamPolicy", role, m
            ),
        )
    return tag["name"] if tag else None


def tagged_columns(apply: bool, tag: str | None) -> None:
    for table, cols in IDENTIFIERS.items():
        t = BQ.get_table(f"{PROJECT}.{table}")
        tagged = lambda f: bool(tag) and f.policy_tags is not None and tag in (f.policy_tags.names or [])
        for f in t.schema:
            if f.name in cols:
                step(apply, tagged(f), f"tag {table}.{f.name} as an {TAG}")
        if apply and tag and not all(tagged(f) for f in t.schema if f.name in cols):
            t.schema = [
                bigquery.SchemaField.from_api_repr(
                    {**f.to_api_repr(), "policyTags": {"names": [tag]}} if f.name in cols else f.to_api_repr()
                )
                for f in t.schema
            ]
            BQ.update_table(t, ["schema"])


def row_policies(apply: bool) -> None:
    ds, table = ROWS_TABLE.split(".")
    url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT}/datasets/{ds}/tables/{table}/rowAccessPolicies"
    have = {r["rowAccessPolicyReference"]["policyId"] for r in call("GET", url).get("rowAccessPolicies", [])}
    policies = {
        "qlsc_risk_two_states": (
            [f"serviceAccount:{sa('qlsc-risk')}"],
            f"state_code IN ({', '.join(repr(s) for s in RISK_STATES)})",
        ),
        "qlsc_all_rows": (ALL_ROWS, "TRUE"),
    }
    for name, (members, where) in policies.items():
        grantees = ", ".join(f'"{m}"' for m in members)
        ddl = (
            f"CREATE OR REPLACE ROW ACCESS POLICY {name} ON `{PROJECT}.{ROWS_TABLE}` "
            f"GRANT TO ({grantees}) FILTER USING ({where})"
        )
        step(
            apply,
            name in have,
            f"row access policy {name} on {ROWS_TABLE}: {where}, for {', '.join(members)}",
            lambda ddl=ddl: BQ.query(ddl).result(),
        )


def main() -> int:
    apply = "--apply" in sys.argv
    print(f"{'Applying' if apply else 'Would apply (--apply to do it)'}, as {OWNER} on {PROJECT}:")
    apis(apply)
    accounts(apply)
    project_roles(apply)
    datasets(apply)
    tagged_columns(apply, policy_tag(apply))
    row_policies(apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
