terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. VPC Peering to Corporate Network
resource "aws_vpc_peering_connection" "corporate" {
  peer_vpc_id   = var.corporate_vpc_id
  vpc_id        = module.vpc.vpc_id
  auto_accept   = true

  tags = {
    Name = "papertoprod-enterprise-peering"
  }
}

# 2. VPC for PaperToProd EKS (Isolated)
module "vpc" {
  source = "../../modules/vpc"

  vpc_name = "papertoprod-enterprise-vpc"
  cidr     = var.vpc_cidr

  # No public subnets, NAT gateways only for egress if absolutely needed,
  # or fully air-gapped depending on customer requirements.
  enable_nat_gateway = false
  single_nat_gateway = false
}

# 3. EKS Cluster (Private Endpoints Only)
module "eks" {
  source = "../../modules/eks"

  cluster_name    = "papertoprod-enterprise-cluster"
  cluster_version = "1.29"

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets

  # Disable public access to the EKS API server
  cluster_endpoint_public_access  = false
  cluster_endpoint_private_access = true

  tags = {
    Environment = "enterprise"
    Customer    = var.customer_name
  }
}
