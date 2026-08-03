output "db_instance_endpoint" {
  description = "The connection endpoint"
  value       = module.db_replica.db_instance_endpoint
}

output "db_instance_arn" {
  description = "The ARN of the RDS instance"
  value       = module.db_replica.db_instance_arn
}
