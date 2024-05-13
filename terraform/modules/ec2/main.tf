# Create aws_ami filter to pick up the ami available in your region
data "aws_ami" "amazon-linux-2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm*"]
  }
}

locals {
  ami_id            = var.ami_id == "" ? data.aws_ami.amazon-linux-2.id : var.ami_id
  provisioner_agent = false # https://github.com/hashicorp/terraform/issues/29074#issuecomment-1026919027
}

# ec2 instance
resource "aws_instance" "this" {
  ami                         = local.ami_id
  associate_public_ip_address = true
  instance_type               = var.instance_type

  # it's better to explicitly declare this (otherwise it gets made anyways with defaults)
  dynamic "root_block_device" {
    for_each = [var.volume_size]
    content {
      encrypted   = true
      volume_size = var.volume_size
      tags = {
        Name = "${var.namespace}-block-device"
      }
    }
  }

  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.ec2.id]

  tags = {
    Name = "${var.namespace}"
  }

  # copy setup.sh to EC2 for use there
  provisioner "file" {
    source      = "${path.module}/setup.sh"
    destination = "/home/${var.server_user}/setup.sh"
    connection {
      type        = "ssh"
      user        = var.server_user
      private_key = file("${var.key_name}.pem")
      host        = self.public_ip
      agent       = local.provisioner_agent
    }
  }

  # run setup script for installing desired software on EC2
  provisioner "remote-exec" {
    script = "${path.module}/setup.sh"
    connection {
      type        = "ssh"
      user        = var.server_user
      private_key = file("${var.key_name}.pem")
      host        = self.public_ip
      agent       = local.provisioner_agent
    }
  }

  lifecycle {
    ignore_changes = [ami]
  }
}

# https://www.middlewareinventory.com/blog/terraform-aws-example-ec2/
resource "aws_security_group" "ec2" {
  name = "${var.namespace}-ec2"

  # only allow traffic from specified ports
  dynamic "ingress" {
    for_each = var.ingress_ports
    iterator = cur # name of var being iterated

    content {
      from_port   = cur.value
      protocol    = "tcp"
      to_port     = cur.value
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  # permit egress to anywhere
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}
