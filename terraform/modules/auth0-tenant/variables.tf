variable "env_name" {
  type        = string
  description = "Name of this deployment environment (e.g. 'TST' | 'ACC' | 'PRD')."
}

variable "site_url" {
  type        = string
  description = "URL of the running website."
}

variable "domain" {
  type        = string
  description = "auth0 domain to use e.g. 'change-me.us.auth0.com'"
}

variable "tf_client_id" {
  type        = string
  description = "client id of 'Terraform Auth0 Provider' application"
}

variable "email_support" {
  description = "Support email for auth0 related issues."
  type        = string
}
