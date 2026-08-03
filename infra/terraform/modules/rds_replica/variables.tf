variable "identifier" {
  type        = string
  description = "The name of the RDS instance"
}

variable "replicate_source_db" {
  type        = string
  description = "The ARN of the source DB instance"
}

variable "instance_class" {
  type        = string
  description = "The instance type of the RDS instance"
}

variable "db_subnet_group_name" {
  type        = string
  description = "Name of DB subnet group"
}

variable "vpc_security_group_ids" {
  type        = list(string)
  description = "List of VPC security groups to associate"
}

variable "tags" {
  type        = map(string)
  description = "A mapping of tags to assign to all resources"
  default     = {}
}
