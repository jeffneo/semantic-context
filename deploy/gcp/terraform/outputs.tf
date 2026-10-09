output "bucket" {
  value = module.runtime.bucket
}

output "databases" {
  description = "Each instance's private address: where the composite's aliases and the demo service point."
  value       = module.runtime.databases
}

output "url" {
  description = "Where the demo is."
  value       = module.runtime.url
}

output "image_repository" {
  value = module.runtime.image_repository
}
