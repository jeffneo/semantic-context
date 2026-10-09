# What a machine fetches at boot: the Virtual Graph's model and jars, and (next) the database dumps. Private; the data-source service account reads it.
resource "google_storage_bucket" "demo" {
  name                        = "${var.project}-qlsc-demo"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true # nothing here is the only copy: the model, jars and dumps are put here from the checkout (scripts/cloud publish, dump)
  versioning {
    enabled = true
  }
}

resource "google_storage_bucket_iam_member" "read" {
  bucket = google_storage_bucket.demo.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.data_source_service_account}"
}
