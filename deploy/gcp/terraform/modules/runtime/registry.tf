# The demo image lives here; the machines and the service read it as the data-source service account.
resource "google_artifact_registry_repository" "demo" {
  repository_id = "qlsc-demo"
  location      = var.region
  format        = "DOCKER"
  description   = "The hosted demo's image"
}

resource "google_artifact_registry_repository_iam_member" "read" {
  repository = google_artifact_registry_repository.demo.name
  location   = var.region
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${var.data_source_service_account}"
}
