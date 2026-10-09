# One machine per database instance, each running its Neo4j in a container, with the data-source service account attached: the machine's own identity is how
# Virtual Graph reaches BigQuery, and how every machine reads the bucket and the secrets. The boot script is the same for all; the role says which it is.

# An address of its own for each machine, kept when the machine is replaced: the composite's aliases and the demo service name it.
resource "google_compute_address" "db" {
  for_each     = var.databases
  name         = "db-${each.key}"
  subnetwork   = var.subnet_id
  address_type = "INTERNAL"
  region       = var.region
}

resource "google_compute_instance" "db" {
  for_each     = var.databases
  name         = "db-${each.key}"
  machine_type = each.value.machine_type
  zone         = var.zone
  tags         = ["qlsc-db"]
  labels       = { app = "qlsc-demo", role = each.key }

  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = each.value.disk_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = var.subnet_id # no access_config: no public address
    network_ip = google_compute_address.db[each.key].address
  }

  service_account {
    email  = var.data_source_service_account
    scopes = ["cloud-platform"]
  }

  metadata = {
    enable-oslogin = "TRUE"
    startup-script = file("${path.module}/../../../vm/boot.sh")
    role           = each.key
    bucket         = google_storage_bucket.demo.name
    heap           = each.value.heap
    image          = each.value.image
    license        = var.neo4j_license_agreement
    database       = each.value.database
    # where the composite's aliases point (only the vg machine reads them)
    semantic_host = google_compute_address.db["semantic"].address
    memory_host   = google_compute_address.db["memory"].address
  }

  # `debian-12` is a family: Google moves it on with each patch, and a machine already made must not be rebuilt for that (the disk is the database's). A new
  # image is taken deliberately: `terraform apply -replace='google_compute_instance.db["<role>"]'`.
  lifecycle {
    ignore_changes = [boot_disk[0].initialize_params[0].image]
  }

  depends_on = [google_storage_bucket_iam_member.read, google_secret_manager_secret_iam_member.read]
}
