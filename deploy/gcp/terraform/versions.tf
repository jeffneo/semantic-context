terraform {
  required_version = ">= 1.9"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
  # State lives in a bucket of its own, named at init (scripts/cloud does it): `terraform init -backend-config="bucket=<name>"`.
  backend "gcs" {
    prefix = "qlsc-demo"
  }
}

provider "google" {
  project = var.project
  region  = var.region
  # Quota and billing go to the project being deployed, whatever project the signed-in user's credentials were made under.
  user_project_override = true
  billing_project       = var.project
}
