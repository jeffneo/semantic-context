# The parts of the network that go with the machines: NAT (the databases have no public address, and reach the internet, the image registry and the package mirror, only
# outward, through it) and the firewall rules. The network and its subnet are the root's: they outlive this module.

resource "google_compute_router" "demo" {
  name    = "qlsc-demo"
  network = var.network_id
  region  = var.region
}

resource "google_compute_router_nat" "demo" {
  name                               = "qlsc-demo"
  router                             = google_compute_router.demo.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# Bolt between the machines and whatever else is in the subnet (the demo service reaches it by Direct VPC egress, with an address in this subnet).
resource "google_compute_firewall" "bolt_internal" {
  name          = "qlsc-demo-bolt-internal"
  network       = var.network_name
  source_ranges = [var.subnet_cidr]
  target_tags   = ["qlsc-db"]
  allow {
    protocol = "tcp"
    ports    = ["7687"]
  }
}

# A shell on a machine, only through Identity-Aware Proxy (Google's range), and bolt through it when debugging.
resource "google_compute_firewall" "iap" {
  name          = "qlsc-demo-iap"
  network       = var.network_name
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["qlsc-db"]
  allow {
    protocol = "tcp"
    ports    = var.debug_bolt_over_iap ? ["22", "7687"] : ["22"]
  }
}
