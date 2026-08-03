# infra/terraform/modules/vpc/variables.tf
variable "name" {
  type        = string
  description = "Name to be used on all the resources as identifier"
}
variable "cidr" {
  type        = string
  description = "The CIDR block for the VPC"
}
variable "azs" {
  type        = list(string)
  description = "A list of availability zones in the region"
}
variable "private_subnets" {
  type        = list(string)
  description = "A list of private subnets inside the VPC"
}
variable "public_subnets" {
  type        = list(string)
  description = "A list of public subnets inside the VPC"
}
variable "tags" {
  type        = map(string)
  default     = {}
}
