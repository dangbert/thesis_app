output "clients" {
  sensitive   = true
  description = "Names (normalized) of auth0 clients mapped to their ID name secret."
  value = {
    backend = {
      id     = data.auth0_client.backend.client_id
      secret = data.auth0_client.backend.client_secret
      name   = data.auth0_client.backend.name
    },
  }
}

output "domain" {
  description = "Base URL for this tenant's domnain e.g. 'change-me.us.auth0.com'"
  value       = var.domain
}

output "is_http" {
  value = local.is_http
}