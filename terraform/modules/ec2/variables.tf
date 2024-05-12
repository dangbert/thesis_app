variable "namespace" {
  type = string
}

variable "key_name" {
  type = string
}

variable "instance_type" {
  default     = "t2.micro"
  type        = string
  description = "https://aws.amazon.com/ec2/instance-types/"
}

variable "ami_id" {
  default     = ""
  type        = string
  description = "ID of desired Amazon Machine Image to use (omit for automatic selection). "
}

variable "volume_size" {
  default     = 30
  type        = number
  description = "GiB of (root) block volume for EC2 instance."
}

variable "volume_id" {
  default     = null
  type        = string
  description = "(Optional) name of existing EBS volume to use (instead of a new one)."
}

variable "ingress_ports" {
  default = [22]
  #default     = [22, 80, 443] # note all use tcp
  type        = list(number)
  description = "list of ports to expose for ingress"
}