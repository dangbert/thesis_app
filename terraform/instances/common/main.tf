terraform {
  backend "s3" {
    bucket         = "dangbert-tf-backend"
    dynamodb_table = "dangbert-tf-backend-lock"
    region         = "us-west-2"
    key            = "thesis/common/terraform.tfstate"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "aws_region" {
  description = "The AWS region to deploy to"
  type        = string
  default     = "eu-west-1"
}

variable "email_domain" {
  description = "The domain name from which emails are sent, this should match the domain you manually verify on AWS SES e.g. 'example.com'"
  type        = string
  default     = "ezfeedback.engbert.me"
}

variable "from_email" {
  description = "The email address from which emails can be sent"
  type        = string
  default     = "notifications@ezfeedback.engbert.me"
}

locals {
  aws = {
    region  = "eu-west-1"
    profile = "default"
  }
  tags          = {}
  templates_dir = "${path.module}/email-templates"
  ses_templates = [for file in fileset(local.templates_dir, "*.html") : "${local.templates_dir}/${file}"]

  env_name  = basename(abspath(path.module))
  namespace = "ezfeedback-${lower(local.env_name)}"
}

resource "aws_ses_domain_identity" "this" {
  domain = var.email_domain
}

resource "aws_ses_configuration_set" "email_failures" {
  name = "${local.namespace}-email-failures"
  delivery_options {
    tls_policy = "Require"
  }
}

resource "aws_ses_event_destination" "sns" {
  name                   = "${local.namespace}-ses"
  configuration_set_name = aws_ses_configuration_set.email_failures.name
  enabled                = true
  matching_types         = ["renderingFailure", "reject", "bounce", "complaint", "delivery"]

  sns_destination {
    topic_arn = aws_sns_topic.ses.arn
  }
}

resource "aws_sns_topic" "ses" {
  name         = "${local.namespace}-ses-alert"
  display_name = "SES alert (failed email)"
  tags         = local.tags
}


provider "aws" {
  region = local.aws.region
}


# MARK: SES templates:
# (magically) create an SES template for each file in the ses temlates dir
resource "aws_ses_template" "templates" {
  for_each = { for file in local.ses_templates : file => file }
  name     = "${local.namespace}-${element(split(".", basename(each.value)), 0)}"
  subject  = "{{subject}}"
  text     = "{{message}}"
  # (tags unsupported)
  html = file(each.value)
}

# https://docs.aws.amazon.com/ses/latest/dg/sending-authorization-policy-examples.html
resource "aws_iam_policy" "ses_send" {
  name        = "${local.namespace}-ses-send"
  description = "Allow sending SES emails from ${var.from_email}"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "ses:SendRawEmail",
          "ses:SendEmail"
        ],
        "Resource" : aws_ses_domain_identity.this.arn,
        "Condition" : {
          "StringLike" : {
            "ses:FromAddress" : var.from_email,
          }
        }
      }
    ]
  })
}

output "ses" {
  value = {
    templates   = [for t in aws_ses_template.templates : t.name]
    config_sets = [aws_ses_configuration_set.email_failures.name]
    iam = {
      send_arn = aws_iam_policy.ses_send.arn
    }
    from_email = var.from_email
  }
}