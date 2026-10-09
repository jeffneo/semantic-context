output "bucket" {
  value = google_storage_bucket.demo.name
}

output "databases" {
  description = "Each instance's private address: where the composite's aliases and the demo service point."
  value       = { for k, v in google_compute_instance.db : k => v.network_interface[0].network_ip }
}

output "url" {
  description = "Where the demo is."
  value       = var.demo_image == "" ? null : google_cloud_run_v2_service.demo[0].uri
}

output "image_repository" {
  value = "${var.region}-docker.pkg.dev/${var.project}/${google_artifact_registry_repository.demo.repository_id}"
}
