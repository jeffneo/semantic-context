# The page and its live panels: one container (docker/demo/Dockerfile), scaled to zero when nobody is there, capped when they are. It reaches the three
# databases over the private network (Direct VPC egress: an address in the subnet, no connector to run) and BigQuery as the service account it runs as.

locals {
  # Where everything is, over this deployment's private addresses (QLSC_OVERRIDES: merged over the example's estate file).
  overrides = jsonencode({
    neo4j      = { uri = "bolt://${google_compute_address.db["semantic"].address}:7687" }
    memory     = { neo4j = { uri = "bolt://${google_compute_address.db["memory"].address}:7687" } }
    virtualize = { neo4j = { uri = "bolt://${google_compute_address.db["vg"].address}:7687" } }
    warehouse  = { identity = "ambient" }
  })
  # secret environment variables of the service and the job: name in the process -> the secret that holds it
  secret_env = {
    NEO4J_PASSWORD           = "qlsc-demo-neo4j-password"
    ANTHROPIC_API_KEY        = "qlsc-demo-anthropic-api-key"
    AZURE_OPENAI_API_KEY     = "qlsc-demo-azure-openai-api-key"
    AZURE_OPENAI_ENDPOINT    = "qlsc-demo-azure-openai-endpoint"
    AZURE_OPENAI_API_VERSION = "qlsc-demo-azure-openai-api-version"
  }
}

resource "google_cloud_run_v2_service" "demo" {
  count               = var.demo_image == "" ? 0 : 1
  name                = "qlsc-demo"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account                  = var.data_source_service_account
    timeout                          = "420s" # a command may wait up to 120 s for a place, then runs up to 240 s
    max_instance_request_concurrency = 16

    scaling {
      min_instance_count = var.demo_min_instances
      max_instance_count = var.demo_max_instances
    }

    vpc_access {
      egress = "PRIVATE_RANGES_ONLY" # only the databases go through the network; BigQuery and the rest leave as they do
      network_interfaces {
        network    = var.network_name
        subnetwork = var.subnet_name
      }
    }

    containers {
      image = var.demo_image
      resources {
        limits   = { cpu = "4", memory = "4Gi" }
        cpu_idle = true # billed while a request is being served
      }
      startup_probe {
        http_get {
          path = "/healthz"
        }
        period_seconds    = 3
        failure_threshold = 20
      }

      env {
        name  = "QLSC_OVERRIDES"
        value = local.overrides
      }
      # The estate's file holds a placeholder for the project: this is the real one (no committed file names it).
      env {
        name  = "QLSC_GCP_PROJECT"
        value = var.project
      }
      env {
        name  = "QLSC_DEMO_COMMANDS_AT_ONCE"
        value = tostring(var.demo_commands_at_once)
      }
      # The keys are this deployment's own, with their limits set at the provider: a question the cache does not hold is then answered, at most as far as the limits allow.
      dynamic "env" {
        for_each = local.secret_env
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.demo[env.value].secret_id
              version = "latest"
            }
          }
        }
      }
      # The pass-through's signing key, as the file the image links to (/secrets/passthrough/passthrough.key).
      volume_mounts {
        name       = "passthrough"
        mount_path = "/secrets/passthrough"
      }
    }

    volumes {
      name = "passthrough"
      secret {
        secret = google_secret_manager_secret.demo["qlsc-demo-passthrough-key"].secret_id
        items {
          version = "latest"
          path    = "passthrough.key"
        }
      }
    }
  }

  # Cloud Run reports the service-level scaling it defaults (a manual count of 0): not ours, and a standing "1 to change" hides real changes.
  lifecycle {
    ignore_changes = [scaling]
  }

  depends_on = [
    google_artifact_registry_repository_iam_member.read,
    google_secret_manager_secret_iam_member.read,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.demo_image != "" && var.demo_public ? 1 : 0
  name     = google_cloud_run_v2_service.demo[0].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# The memory sweep (qlsc memory sweep, plans/2026-10-08-memory-retention.md): fetched rows go once they are older than memory.retain.fetched_days. A job of the same
# image, run every hour by Cloud Scheduler.
resource "google_cloud_run_v2_job" "sweep" {
  count               = var.demo_image == "" ? 0 : 1
  name                = "qlsc-memory-sweep"
  location            = var.region
  deletion_protection = false

  template {
    template {
      service_account = var.data_source_service_account
      timeout         = "900s"
      max_retries     = 1
      vpc_access {
        egress = "PRIVATE_RANGES_ONLY"
        network_interfaces {
          network    = var.network_name
          subnetwork = var.subnet_name
        }
      }
      containers {
        image   = var.demo_image
        command = ["qlsc"]
        args    = ["memory", "sweep"]
        env {
          name  = "QLSC_CONFIG"
          value = "/app/examples/fennmoor-bank/estate.yaml"
        }
        env {
          name  = "QLSC_OVERRIDES"
          value = local.overrides
        }
        env {
          name  = "QLSC_GCP_PROJECT"
          value = var.project
        }
        env {
          name = "NEO4J_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.demo["qlsc-demo-neo4j-password"].secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  depends_on = [google_artifact_registry_repository_iam_member.read, google_secret_manager_secret_iam_member.read]
}

resource "google_cloud_run_v2_job_iam_member" "sweep_runs" {
  count    = var.demo_image == "" ? 0 : 1
  name     = google_cloud_run_v2_job.sweep[0].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.data_source_service_account}"
}

resource "google_cloud_scheduler_job" "sweep" {
  count     = var.demo_image == "" ? 0 : 1
  name      = "qlsc-memory-sweep"
  region    = var.region
  schedule  = "0 * * * *"
  time_zone = "Etc/UTC"

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project}/locations/${var.region}/jobs/${google_cloud_run_v2_job.sweep[0].name}:run"
    oauth_token {
      service_account_email = var.data_source_service_account
    }
  }

  depends_on = [google_cloud_run_v2_job_iam_member.sweep_runs]
}
