#################################################################################
# This file configures all resources needed for managing our auth0 tenants with Terraform.
# See architecture-docs/auth0-setup.md for more info.
#################################################################################

terraform {
  required_providers {
    auth0 = {
      source  = "auth0/auth0"
      version = ">= 1.0.0"
    }
  }
}

locals {
  # TODO: change later:
  logo_url             = ""
  favicon_url          = ""
  login_background_url = ""

  backend_callback_url = "${var.site_url}/api/v1/auth/callback"
  # audience comes from `Applications > APIs`
  audience      = "https://${var.domain}/api/v2/"
  is_prd        = lower(var.env_name) == "prd"
  friendly_name = "Feedback Tool${local.is_prd ? "" : " (${var.env_name})"}"
  is_http       = startswith(var.site_url, "http://")
}

resource "auth0_tenant" "this" {
  allow_organization_name_in_authentication_api = false
  enabled_locales                               = ["en"]
  friendly_name                                 = local.friendly_name
  picture_url                                   = local.logo_url
  sandbox_version                               = "16"
  support_email                                 = var.email_support
  support_url                                   = null
  #default_redirection_uri = var.site_url

  flags {
    # don't auto-enable existing connections when new clients are created:
    enable_client_connections = false
  }
}

#### clients: ####
resource "auth0_client" "backend" {
  app_type            = "regular_web"
  callbacks           = [local.backend_callback_url]
  allowed_logout_urls = [var.site_url]
  allowed_origins     = [var.site_url]
  web_origins         = [var.site_url]
  logo_uri            = local.logo_url
  initiate_login_uri  = !local.is_http ? var.site_url : ""
  name                = local.friendly_name

  sso             = true
  oidc_conformant = true
  jwt_configuration {
    # IMPORTANT! the default algorith, "HS256" leads to 'ValueError: Invalid JSON Web Key Set' upon calling  'await oauth.auth0.authorize_access_token(request)' in auth.py
    # due to kid field missing in the decoded token ('authlib/jose/rfc7517/key_set.py', line 29, in find_by_kid)
    # https://community.auth0.com/t/rs256-vs-hs256-jwt-signing-algorithms/58609
    alg = "RS256"
  }
}

data "auth0_client" "backend" {
  name = auth0_client.backend.name
}
##################

# permissions for backend application
resource "auth0_client_grant" "backend" {
  audience  = local.audience
  client_id = auth0_client.backend.client_id
  scopes    = ["read:users", "update:users", "delete:users", "create:users"]
}


#### define user sources (e.g. databases, passwordless, socials, etc): ####
# https://registry.terraform.io/providers/auth0/auth0/latest/docs/resources/connection#google-oauth2-connection

# TODO
#  terraform import module.auth0_tenant.auth0_connection.google con_id_changeme
resource "auth0_connection" "google" {
  is_domain_connection = false
  metadata             = {}
  name                 = "google-oauth2"
  strategy             = "google-oauth2"

  options {
    client_id         = var.google_oauth.client_id
    client_secret     = var.google_oauth.client_secret
    allowed_audiences = var.additional_audiences
    # allow user management over API
    # api_enable_users = true
    disable_signup = var.disable_signup
    # domain_aliases                       = []
    scopes = [
      "email",
      "profile",
    ]
  }
}

resource "auth0_connection" "passwordless_email" {
  strategy = "email"
  name     = "email"

  display_name         = null
  is_domain_connection = false
  metadata             = {}
  show_as_button       = null

  options {
    brute_force_protection = true
    disable_signup         = var.disable_signup
    name                   = "email"
    syntax                 = "liquid"

    # from     = var.email_from
    subject = "Welcome to {{ application.name }}"
    # template = file("${local.templates_dir}/passwordless-template.html")

    # https://auth0.com/docs/authenticate/passwordless/authentication-methods/email-otp
    totp {
      # length of the emailed login code:
      length = 6
      # seconds users have to enter the emailed login code:
      # NOTE: if you update this, also update passwordless-email-template.html
      time_step = 60 * 60 # 1 hour
    }
  }
  count = var.with_passwordless ? 1 : 0
}

resource "auth0_connection_clients" "passwordless_email" {
  connection_id   = resource.auth0_connection.passwordless_email[0].id
  enabled_clients = [auth0_client.backend.id]
  count           = var.with_passwordless ? 1 : 0
}

# same as the UI page "Authentication" > "Authentication Profile"
resource "auth0_prompt" "prompts" {
  # don't show password field on initial login page
  identifier_first               = true
  universal_login_experience     = "new"
  webauthn_platform_first_factor = false
}

##################

resource "auth0_branding" "branding" {
  favicon_url = local.favicon_url
  logo_url    = local.logo_url
  count       = (local.favicon_url != "" && local.logo_url != "") ? 1 : 0
}

# TODO: import default theme into terraform?
#   e.g. `terraform import module.cbm_auth0.auth0_branding_theme.theme "default"`
#resource "auth0_branding_theme" "theme" {

resource "auth0_attack_protection" "attack_protection" {
  # use the defaults
}
