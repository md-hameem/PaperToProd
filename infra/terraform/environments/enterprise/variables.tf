variable "aws_region" {
  description = "AWS region for the enterprise deployment"
  type        = string
  default     = "us-east-1"
}

variable "customer_name" {
  description = "Name of the enterprise customer"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the PaperToProd isolated VPC"
  type        = string
  default     = "10.100.0.0/16"
}

variable "corporate_vpc_id" {
  description = "VPC ID of the customer's corporate network for peering"
  type        = string
}
