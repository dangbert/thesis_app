output "public_ip" {
  value = aws_instance.this.public_ip
}

output "private_ip" {
  value = aws_instance.this.private_ip
}

output "instance_id" {
  value = aws_instance.this.id
}

output "root_block_device_id" {
  value = aws_instance.this.root_block_device.*.volume_id
}

output "ebs_block_device_id" {
  value = aws_instance.this.ebs_block_device.*.volume_id
}

output "ami_id" {
  value       = local.ami_id
  description = "ID of Amazon Machine Image that was used for this EC2 instance."
}

output "server_user" {
  value       = var.server_user
  description = "mirrors var.server_user"
}