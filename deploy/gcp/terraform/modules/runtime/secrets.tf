# The secrets exist here, empty; their values are put there by `scripts/cloud secrets` and never pass through Terraform, whose state would hold them in the clear.
locals {
  secrets = toset([
    "qlsc-demo-neo4j-password",
    "qlsc-demo-passthrough-key",
    "qlsc-demo-keystore-password",
    # this deployment's own keys, with limits set at the provider (scripts/cloud secrets reads them from deploy/gcp/.env)
    "qlsc-demo-anthropic-api-key",
    "qlsc-demo-azure-openai-api-key",
    "qlsc-demo-azure-openai-endpoint",
    "qlsc-demo-azure-openai-api-version",
  ])
}

resource "google_secret_manager_secret" "demo" {
  for_each  = local.secrets
  secret_id = each.key
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "read" {
  for_each  = local.secrets
  secret_id = google_secret_manager_secret.demo[each.key].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.data_source_service_account}"
}
