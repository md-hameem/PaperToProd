module "db" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = var.identifier

  engine               = "postgres"
  engine_version       = "15.3"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = var.instance_class

  allocated_storage     = 100
  max_allocated_storage = 500

  db_name  = var.db_name
  username = var.username
  password = var.password
  port     = 5432

  multi_az               = true
  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = var.vpc_security_group_ids

  maintenance_window      = "Mon:00:00-Mon:03:00"
  backup_window           = "03:00-06:00"
  backup_retention_period = 7 # Daily snapshots

  # WAL archiving and automated backups
  copy_tags_to_snapshot = true
  skip_final_snapshot   = false
  deletion_protection   = true

  tags = var.tags
}
