# The network is the long-lived part of the deployment: it costs nothing, and the machines and the service come and go on it (module.runtime). `scripts/cloud destroy` leaves it, because
# Cloud Run keeps address blocks reserved in a subnet for a long while after its service is gone, and a subnet cannot be deleted until they are released.
# A /22, so that the blocks left by successive services do not use it up (each is a /28).

resource "google_compute_network" "demo" {
  name                    = "qlsc-demo"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

resource "google_compute_subnetwork" "demo" {
  name                     = "qlsc-demo-${var.region}"
  network                  = google_compute_network.demo.id
  region                   = var.region
  ip_cidr_range            = var.subnet_cidr
  private_ip_google_access = true # Cloud Storage, Secret Manager and the registries without leaving Google's network
}
