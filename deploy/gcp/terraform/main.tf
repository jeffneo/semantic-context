# Everything that goes with the machines and the service: the databases, the service, the registry, the bucket, the secrets, the sweep, NAT and the firewall. A module so that it
# has a lifecycle of its own: `scripts/cloud destroy` removes `module.runtime` and leaves the network and the APIs (this directory's other files).

module "runtime" {
  source = "./modules/runtime"

  project                     = var.project
  region                      = var.region
  zone                        = var.zone
  data_source_service_account = var.data_source_service_account
  databases                   = var.databases
  neo4j_license_agreement     = var.neo4j_license_agreement
  demo_image                  = var.demo_image
  demo_max_instances          = var.demo_max_instances
  demo_min_instances          = var.demo_min_instances
  demo_commands_at_once       = var.demo_commands_at_once
  demo_public                 = var.demo_public
  billing_account             = var.billing_account
  budget_usd                  = var.budget_usd

  network_name = google_compute_network.demo.name
  network_id   = google_compute_network.demo.id
  subnet_name  = google_compute_subnetwork.demo.name
  subnet_id    = google_compute_subnetwork.demo.id
  subnet_cidr  = google_compute_subnetwork.demo.ip_cidr_range

  # the services it uses are enabled first
  depends_on = [google_project_service.apis]
}
