terraform {
  backend "s3" {
    bucket         = "dangbert-tf-backend"
    dynamodb_table = "dangbert-tf-backend-lock"
    region         = "us-west-2"
    key            = "thesis/PRD/terraform.tfstate"
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

variable "aws_region" {
  description = "The AWS region to deploy to"
  type        = string
  default     = "eu-west-1"
}

variable "create_ec2" {
  type        = bool
  description = "set true to create an EC2 instance for deployment"
}

locals {
  aws = {
    region  = var.aws_region
    profile = "default"
  }
  env_name  = basename(abspath(path.module))
  namespace = "ezfeedback-${lower(local.env_name)}"
  common    = data.terraform_remote_state.common.outputs
}

# read data from common environment
data "terraform_remote_state" "common" {
  backend = "s3"
  config = {
    bucket         = "dangbert-tf-backend"
    dynamodb_table = "dangbert-tf-backend-lock"
    region         = "us-west-2"
    key            = "thesis/common/terraform.tfstate"
  }
}


provider "aws" {
  region = local.aws.region
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
  site_url = "https://ezfeedback.engbert.me"

  tf_client_id         = var.auth0_provider.client_id
  email_support        = "d.engbert@student.vu.nl"
  disable_signup       = false
  additional_audiences = []

  google_oauth = var.google_oauth
}

module "ssh_key" {
  source    = "../../modules/ssh-key"
  namespace = local.namespace
  count     = var.create_ec2 ? 1 : 0
}

module "ec2" {
  source    = "../../modules/ec2"
  namespace = local.namespace
  key_name  = module.ssh_key[0].key_name

  # ubuntu 24.04 LTS, amd64, eu-west-1 (from https://cloud-images.ubuntu.com/locator/ec2/)
  ami_id        = "ami-0776c814353b4814d"
  server_user   = "ubuntu"
  instance_type = "t2.micro"
  volume_size   = 45
  ingress_ports = [22, 443, 80]
  policies      = [local.common.ses.iam.send_arn]
  count         = var.create_ec2 ? 1 : 0
}

# attaching SES policy directly to EC2 doesn't seem to help the Docker service
# so explicitly creating credentials as env vars
resource "aws_iam_user" "this" {
  name = "${local.namespace}-user"
}

resource "aws_iam_access_key" "this" {
  user = aws_iam_user.this.name
}

resource "aws_iam_user_policy_attachment" "ses" {
  user       = aws_iam_user.this.name
  policy_arn = local.common.ses.iam.send_arn
}

output "auth0" {
  sensitive = true
  value     = module.auth0_tenant
}

output "ec2" {
  value = !var.create_ec2 ? {} : {
    ssh_cmds = {
      ssh = "ssh -i ${module.ssh_key[0].key_name}.pem ${module.ec2[0].server_user}@${module.ec2[0].public_ip}"
      scp = "scp -i ${module.ssh_key[0].key_name}.pem file.txt ${module.ec2[0].server_user}@${module.ec2[0].public_ip}:"
    }
    aws_cmds = {
      stop   = "aws ec2 stop-instances --instance-ids ${module.ec2[0].instance_id} --region ${local.aws.region} --profile ${local.aws.profile}"
      start  = "aws ec2 start-instances --instance-ids ${module.ec2[0].instance_id} --region ${local.aws.region} --profile ${local.aws.profile}"
      status = "aws ec2 describe-instance-status --instance-ids ${module.ec2[0].instance_id} --region ${local.aws.region} --profile ${local.aws.profile}"
    }
  }
}

output "iam_credentials" {
  description = "Credentials needed by this environment (to use SES)."
  sensitive   = true
  value = {
    access_key_id     = aws_iam_access_key.this.id
    secret_access_key = aws_iam_access_key.this.secret
  }
}