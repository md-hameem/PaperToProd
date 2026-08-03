provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "dr"
  region = "us-west-2"
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

  azs              = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets   = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  database_subnets = ["10.0.201.0/24", "10.0.202.0/24", "10.0.203.0/24"]

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
  tags        = local.tags

  replication_enabled                = true
  replication_destination_bucket_arn = module.s3_bucket_dr.bucket_arn
}

# -----------------------------------------------------------------------------
# DR ENVIRONMENT (us-west-2)
# -----------------------------------------------------------------------------

module "vpc_dr" {
  source = "../../modules/vpc"
  providers = { aws = aws.dr }

  name = "${local.name}-dr"
  cidr = "10.1.0.0/16"

  azs              = ["us-west-2a", "us-west-2b", "us-west-2c"]
  private_subnets  = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
  public_subnets   = ["10.1.101.0/24", "10.1.102.0/24", "10.1.103.0/24"]
  database_subnets = ["10.1.201.0/24", "10.1.202.0/24", "10.1.203.0/24"]

  tags = merge(local.tags, { Environment = "prod-dr" })
}

module "s3_bucket_dr" {
  source = "../../modules/s3"
  providers = { aws = aws.dr }

  bucket_name = "${local.name}-artifacts-dr"
  tags        = merge(local.tags, { Environment = "prod-dr" })
}

module "rds_replica_dr" {
  source = "../../modules/rds_replica"
  providers = { aws = aws.dr }

  identifier          = "${local.name}-dr"
  replicate_source_db = module.rds.db_instance_arn
  instance_class      = "db.m5.large"

  db_subnet_group_name   = module.vpc_dr.database_subnet_group_name
  vpc_security_group_ids = [module.vpc_dr.default_security_group_id]

  tags = merge(local.tags, { Environment = "prod-dr" })
}
