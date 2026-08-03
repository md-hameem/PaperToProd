variable "identifier" { type = string }
variable "instance_class" { type = string }
variable "db_name" { type = string }
variable "username" { type = string }
variable "password" { type = string }
variable "db_subnet_group_name" { type = string }
variable "vpc_security_group_ids" { type = list(string) }
variable "tags" { type = map(string) }
