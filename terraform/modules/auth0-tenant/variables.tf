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

variable "disable_signup" {
  description = "Whether to disable new user signup"
  type        = bool
}

variable "additional_audiences" {
  description = "For dev tenant purposes, you can pass in a localhost url"
  type        = list(string)
  default     = []
}

variable "with_passwordless" {
  description = "Whether to enable passwordless connections"
  type        = bool
  default     = false
}

variable "google_oauth" {
  description = "Your google oauth credentials, see installation steps here https://marketplace.auth0.com/integrations/google-social-connectio"
  sensitive   = true
  type = object({
    client_id     = string
    client_secret = string
  })
  default = {
    client_id     = ""
    client_secret = ""
  }
}