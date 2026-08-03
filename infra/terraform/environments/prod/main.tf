provider "aws" {
  region = "us-east-1"
}

locals {
  name = "papertoprod-prod"
  tags = {
    Environment = "prod"
    Project     = "papertoprod"
  }
}

module "vpc" {
  source = "../../modules/vpc"

  name = local.name
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  tags = local.tags
}

module "eks" {
  source = "../../modules/eks"

  cluster_name    = local.name
  cluster_version = "1.27"

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets

  tags = local.tags
}

module "rds" {
  source = "../../modules/rds"

  identifier = local.name
  instance_class = "db.m5.large"
  db_name = "papertoprod"
  username = "ptp_admin"
  password = "mockpassword_to_be_replaced_by_secrets_manager" # Phase 2.15

  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [module.vpc.default_security_group_id] # Should create specific SG

  tags = local.tags
}

module "s3_bucket" {
  source = "../../modules/s3"

  bucket_name = "${local.name}-artifacts"
  tags = local.tags
}
