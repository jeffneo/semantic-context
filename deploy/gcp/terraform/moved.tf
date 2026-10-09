# Resources this deployment already had, before the runtime was a module: moved in the state, not rebuilt.

moved {
  from = google_storage_bucket.demo
  to   = module.runtime.google_storage_bucket.demo
}

moved {
  from = google_storage_bucket_iam_member.read
  to   = module.runtime.google_storage_bucket_iam_member.read
}

moved {
  from = google_secret_manager_secret.demo
  to   = module.runtime.google_secret_manager_secret.demo
}

moved {
  from = google_secret_manager_secret_iam_member.read
  to   = module.runtime.google_secret_manager_secret_iam_member.read
}

moved {
  from = google_compute_address.db
  to   = module.runtime.google_compute_address.db
}

moved {
  from = google_compute_instance.db
  to   = module.runtime.google_compute_instance.db
}

moved {
  from = google_artifact_registry_repository.demo
  to   = module.runtime.google_artifact_registry_repository.demo
}

moved {
  from = google_artifact_registry_repository_iam_member.read
  to   = module.runtime.google_artifact_registry_repository_iam_member.read
}

moved {
  from = google_cloud_run_v2_service.demo
  to   = module.runtime.google_cloud_run_v2_service.demo
}

moved {
  from = google_cloud_run_v2_service_iam_member.public
  to   = module.runtime.google_cloud_run_v2_service_iam_member.public
}

moved {
  from = google_cloud_run_v2_job.sweep
  to   = module.runtime.google_cloud_run_v2_job.sweep
}

moved {
  from = google_cloud_run_v2_job_iam_member.sweep_runs
  to   = module.runtime.google_cloud_run_v2_job_iam_member.sweep_runs
}

moved {
  from = google_cloud_scheduler_job.sweep
  to   = module.runtime.google_cloud_scheduler_job.sweep
}

moved {
  from = google_billing_budget.demo
  to   = module.runtime.google_billing_budget.demo
}

moved {
  from = google_compute_router.demo
  to   = module.runtime.google_compute_router.demo
}

moved {
  from = google_compute_router_nat.demo
  to   = module.runtime.google_compute_router_nat.demo
}

moved {
  from = google_compute_firewall.bolt_internal
  to   = module.runtime.google_compute_firewall.bolt_internal
}

moved {
  from = google_compute_firewall.iap
  to   = module.runtime.google_compute_firewall.iap
}

