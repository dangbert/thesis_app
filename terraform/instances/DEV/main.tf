terraform {
  backend "s3" {
    bucket         = "dangbert-tf-backend"
    dynamodb_table = "dangbert-tf-backend-lock"
    region         = "us-west-2"
    key            = "thesis/DEV/terraform.tfstate"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    auth0 = {
      source  = "auth0/auth0"
      version = ">= 1.0.0"
    }
  }
}

provider "aws" {
  region = "eu-west-1"
}

provider "auth0" {
  domain        = var.auth0_provider.domain
  client_id     = var.auth0_provider.client_id
  client_secret = var.auth0_provider.client_secret
}

locals {
  env_name  = basename(abspath(path.module))
  namespace = "ezfeedback-${lower(local.env_name)}"
}

variable "auth0_provider" {
  type = object({
    domain        = string
    client_id     = string
    client_secret = string
  })
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


module "auth0_tenant" {
  source   = "../../modules/auth0-tenant"
  domain   = var.auth0_provider.domain
  env_name = local.env_name
  # should match DEV_HOST_PORT in docker-compose.dev.yml
  site_url = "http://localhost:2222"

  tf_client_id         = var.auth0_provider.client_id
  email_support        = "d.engbert@student.vu.nl"
  disable_signup       = false
  additional_audiences = ["http://localhost:8000/"]

  google_oauth = var.google_oauth
}

module "ssh_key" {
  source    = "../../modules/ssh-key"
  namespace = local.namespace
}

module "ec2" {
  source    = "../../modules/ec2"
  namespace = local.namespace
  key_name  = module.ssh_key.key_name

  instance_type = "t2.micro"
  volume_size   = 45
  ingress_ports = [22, 443, 80]
}

output "auth0" {
  sensitive = true
  value     = module.auth0_tenant
}