# deploy/gcp: the demo, hosted

The Fennmoor demo page and its live panels on Google Cloud, so that someone can use them without installing anything. It is also a worked example of how a
three-database Neo4j deployment with a composite database is put on infrastructure: each part in the place that suits what it is. The plan and its reasons are in
[plans/2026-10-08-cloud-deploy.md](../../plans/2026-10-08-cloud-deploy.md).

```bash
scripts/cloud up        # from nothing, or from stopped: about 30 minutes the first time; prints the address
scripts/cloud status
scripts/cloud tunnel    # a way in to the database machines, while it runs
scripts/cloud down      # stops the database machines: about about $30 a month while stopped (the disks); running 24 hours a day, about $180
scripts/cloud destroy   # removes the machines, the service and the rest of what runs; the network stays
scripts/cloud destroy --everything   # and the network too (it waits, up to three hours, for Google to release Cloud Run's addresses in the subnet)
```

## What it is

```
 visitor ──https──▶ Cloud Run `qlsc-demo`   the page's files and the demo server, in one container (docker/demo)
                          │ private network (Direct VPC egress)
         ┌────────────────┼───────────────────────┐
         ▼                ▼                       ▼
    db-semantic        db-memory               db-vg  ───────▶ BigQuery
    the semantic       what agents             Virtual Graph, and the composite `fennmoor`
    layer              remembered              (aliases to the other two, and to its own virtual graph)
```

| Part | Why it is where it is |
|---|---|
| Cloud Run, one service | Stateless, so serverless: scales to zero, costs nothing idle, and is capped (`demo_max_instances`) when busy. |
| Three database machines | Databases are stateful and want their own disk and memory, so each is a small VM running one Neo4j container: no public address, reached only over the private network. The composite is where they meet, which is the pattern worth learning: `db-vg`'s aliases point at the other two over TLS. |
| 100 GB disks | Over-provisioned on purpose: a larger disk gets a larger share of the underlying IO. |
| Data in Cloud Storage | The databases are restored at first boot from a dump (`scripts/cloud dump`), so a machine is disposable: destroy it, and `up` brings it back as it was dumped. |
| No keys | The machines and the service run as one service account (the data source's identity); there is no credentials file anywhere. Virtual Graph reaches BigQuery as that account, and impersonates each principal from it, so the warehouse's own rules apply. |
| Secrets in Secret Manager | The Neo4j and keystore passwords, the pass-through signing key, and the deployment's own model keys. Terraform makes the empty secrets; `scripts/cloud secrets` fills them, so no secret is in Terraform's state. |
| A sweep every hour | Memory keeps what it fetched for six hours (`memory.retain`): a Cloud Run job of the same image runs `qlsc memory sweep`, fired by Cloud Scheduler. |

## What a visitor can do

Open the page and run its examples: nothing to sign in to. The server runs **only the page's own examples** (`ui/dist/presets.json`, which the page's build writes from its
own presets: the same rule as the local page), so a query, question or customer typed by a visitor is refused. For memory's examples the server chooses a customer: one with
calls and card activity that memory does not hold yet, so each visitor's first recall is a real fetch and what they leave expires.

Every question the page offers is answered from the cache that ships in the image. The deployment also holds its **own model keys**, made for it with limits set at the
provider (an Anthropic workspace with a monthly spend cap and rate limits; an Azure OpenAI deployment with a tokens-per-minute quota): a question the cache does not hold is
then answered, at most as far as the limits allow, and the keys are not your own. The service runs several commands at once (`demo_commands_at_once`, a memory limit; a visitor
beyond it waits for a place and is told) and at most `demo_max_instances` copies.

## Using it

- `deploy/gcp/terraform/terraform.tfvars` (not committed; copy `terraform.tfvars.example`) names the project (the service and the sweep get it as `QLSC_GCP_PROJECT`, since the example's estate file holds only a placeholder) and the service account that is the data source's identity.
  Another license for the Neo4j image than the evaluation one is set there too (`neo4j_license_agreement`).
- `deploy/gcp/.env` (not committed) holds the deployment's own `ANTHROPIC_API_KEY`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_VERSION`; `scripts/cloud secrets` writes them to
  Secret Manager (`scripts/cloud secrets --keys` again after a key is rotated). They are not the keys of the checkout's own `.env`. `AZURE_OPENAI_ENDPOINT` is the resource's address,
  `https://<name>.openai.azure.com/`, as in `.env.example`, not the portal's v1 URL; both the tool and `scripts/cloud secrets` refuse the other form by name.
- `scripts/cloud up` needs your gcloud sign-in (a user who may create these things in the project), Terraform, Docker, and the checkout's own stack running
  (`scripts/stack up`), because the data it puts in the cloud is dumped from there. `--yes` skips Terraform's confirmations.
- A budget alert is optional: set `billing_account` (and `budget_usd`, default $200) in `terraform.tfvars`. It emails the billing account's admins as the month's spend reaches 50%, 90% and 100%;
  it warns, it does not stop anything.
- `demo_min_instances` (default 0): the service scales to zero when idle, so the first visitors after a quiet spell wait for a copy to start (a first recall can take about a minute, and a burst of
  visitors may see a connection reset while copies are added). Set it to 1 for an event: a copy stays warm, for about $25 a month while it is set.
- `scripts/cloud tunnel` is the way in to the database machines from your workstation (to query one, or open Browser on it): it opens a firewall rule for Google's tunnel proxy (IAP) on bolt
  while it runs, starts a tunnel to each machine on a local port (7701 semantic, 7702 memory, 7703 Virtual Graph) and prints how to connect; Ctrl-C closes it and removes the rule
  (`scripts/cloud tunnel --close` removes one a killed tunnel left; `status` says if one is open). The machines keep no public address, and who may use it is IAM's
  (`roles/iap.tunnelResourceAccessor`), so the deployment is closed by default and an operator's access is deliberate.
- To change what is deployed: `scripts/cloud image` builds and pushes a new image, then `terraform apply` in `terraform/` rolls it out; `scripts/cloud dump` and
  a `terraform apply -replace='google_compute_instance.db["memory"]'` put new data on a machine (a machine restores only into an empty disk).

## Things to know

- **Memory is shared, and short-lived.** Visitors' `recall` and `exchange` runs write to the one memory database. Each visitor's recall is of a customer of their own, and the hourly
  sweep deletes fetched rows six hours after they were fetched; the audit record (conversations, steps, decisions) is kept. See plans/2026-10-08-memory-retention.md.
- **Bolt between the machines is encrypted but not authenticated as a server** (`neo4j+ssc`: each machine makes a self-signed certificate). On a private network with
  no public addresses that is a small risk; a certificate authority both ends trust, and `neo4j+s`, is the next step.
- **Debian is a moving family** (`debian-12`); a machine already made keeps its image, and a rebuild with a newer one is deliberate (`-replace`, as above).
- **The Virtual Graph machine's first boot** once reported "did not answer" for eleven minutes while Neo4j was in fact up; the same script succeeded on a re-run. It
  is logged now (`gcloud compute instances get-serial-port-output db-vg`); if `up` times out, that is where to look.
- **License.** The images run under the evaluation license unless you set another.
- **The network is kept by `destroy`.** Cloud Run's network egress reserves a /28 in the subnet for a service, and Google releases it only a long while after the service is gone (more than an hour in
  practice, which is why the subnet cannot be deleted at once). The network costs nothing, so `destroy` leaves it and `up` reuses it; the subnet is a /22 so that reservations left behind do not use it up.
- Terraform's provider rejects a plan whose startup script changes while an apply is running: do not edit `vm/boot.sh` during one.

## Files

| | |
|---|---|
| `terraform/` | the long-lived part: the network, its subnet (a /22) and the APIs |
| `terraform/modules/runtime/` | what runs and can be removed and rebuilt: the three machines, NAT and the firewall, the service, the sweep job, the registry, the bucket, the secrets, the optional budget |
| `vm/boot.sh` | what each database machine runs at boot: Docker, the restore, TLS, the container, and on `db-vg` the keystore and the composite |
| `../../docker/demo/` | the demo image |
| `../../scripts/cloud` | `up`, `down`, `destroy`, `status`, and the steps they are made of |
