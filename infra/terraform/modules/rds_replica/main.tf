module "db_replica" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = var.identifier

  # For read replicas, engine and engine_version must match the source,
  # or can be omitted if the module auto-derives from replicate_source_db.
  # We specify replicate_source_db to link it.
  replicate_source_db = var.replicate_source_db

  instance_class = var.instance_class

  port = 5432

  multi_az               = false # Standby region can be single-AZ for cost savings until promoted
  vpc_security_group_ids = var.vpc_security_group_ids

  # Replica doesn't specify db_name, username, password.
  # Subnet group must be created in the DR region.
  db_subnet_group_name = var.db_subnet_group_name

  # Cross-region replica needs automated backups turned on to be promoted later
  backup_retention_period = 7
  skip_final_snapshot     = true

  tags = var.tags
}
