terraform {
  backend "s3" {
    bucket         = "dangbert-tf-backend"
    dynamodb_table = "dangbert-tf-backend-lock"
    region         = "us-west-2"
    key            = "thesis/DEV/terraform.tfstate"
  }

  required_providers {
    auth0 = {
      source  = "auth0/auth0"
      version = ">= 1.0.0"
    }
  }
}

provider "auth0" {
  domain        = var.auth0_provider.domain
  client_id     = var.auth0_provider.client_id
  client_secret = var.auth0_provider.client_secret
}

variable "auth0_provider" {
  type = object({
    domain        = string
    client_id     = string
    client_secret = string
  })
}

locals {
  env_name = basename(abspath(path.module))
}

module "auth0_tenant" {
  source   = "../../modules/auth0-tenant"
  domain   = var.auth0_provider.domain
  env_name = local.env_name
  site_url = "http://localhost:4200"

  tf_client_id  = var.auth0_provider.client_id
  email_support = "d.engbert@student.vu.nl"
}