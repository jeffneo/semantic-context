variable "project" {
  description = "The GCP project the demo is deployed in."
  type        = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "zone" {
  type    = string
  default = "us-central1-a"
}

variable "data_source_service_account" {
  description = "Email of the service account the databases and the demo read the warehouse as (the estate's data-source identity: it holds the principals' token-creator grants). Attached to the machines: no key file exists anywhere."
  type        = string
}

variable "databases" {
  description = "One small VM per database instance, keyed by role. `database` is the Neo4j database it holds (semantic and memory: restored from the dump; vg holds the virtual graph and the composite). `disk_gb` is over-provisioned on purpose: a larger disk gets a larger share of the underlying IO. `heap` is the instance's heap, for the machine's memory."
  type = map(object({
    machine_type = string
    disk_gb      = number
    heap         = string
    image        = string
    database     = optional(string, "")
  }))
  default = {
    semantic = { machine_type = "e2-standard-2", disk_gb = 100, heap = "4G", image = "neo4j:2026.07.1-enterprise", database = "bigquery" } # 8 GB: 4G heap, 2G page cache
    memory   = { machine_type = "e2-standard-2", disk_gb = 100, heap = "4G", image = "neo4j:2026.07.1-enterprise", database = "memory" }
    vg       = { machine_type = "e2-standard-2", disk_gb = 100, heap = "5G", image = "neo4j:2026.09.0-enterprise" } # 8 GB: Virtual Graph ran out of heap at 2G under three concurrent runs
  }
}

variable "neo4j_license_agreement" {
  description = "NEO4J_ACCEPT_LICENSE_AGREEMENT for the instances. `eval` unless you hold another license for the image; set it in your own untracked terraform.tfvars."
  type        = string
  default     = "eval"
}

variable "demo_image" {
  description = "The demo image to run (scripts/cloud image builds it, pushes it and writes this to image.auto.tfvars). Empty: no service yet."
  type        = string
  default     = ""
}

variable "demo_max_instances" {
  description = "The most copies of the demo service that run at once: the cap on what can reach the databases and the warehouse, whatever the traffic."
  type        = number
  default     = 4
}

variable "demo_min_instances" {
  description = "Copies of the service kept running when nobody is there. 0: it scales to zero and costs nothing idle, and the first visitors after a quiet spell wait for a copy to start (about a minute for the first recall). 1 for an event: about $25 a month while it is set."
  type        = number
  default     = 0
}

variable "demo_commands_at_once" {
  description = "How many commands (ask, recall, exchange: each a process of about 300 MB) one copy of the service runs at once; a visitor beyond that waits for a place. Sized to the service's memory."
  type        = number
  default     = 8
}

variable "demo_public" {
  description = "Anyone on the internet may open the service (it holds nothing a visitor can change: only the page's own examples run). Off: only callers with an invoker grant."
  type        = bool
  default     = true
}

variable "billing_account" {
  description = "The billing account's id (XXXXXX-XXXXXX-XXXXXX), to put a budget alert on this project. Empty: no budget. Needs a role on the billing account."
  type        = string
  default     = ""
}

variable "budget_usd" {
  description = "The monthly amount the budget alerts against (at 50%, 90% and 100% of it)."
  type        = number
  default     = 200
}


# What the root gives it: the network it runs on.
variable "network_name" {
  type = string
}

variable "network_id" {
  type = string
}

variable "subnet_name" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "subnet_cidr" {
  type = string
}
