module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  vpc_id                   = var.vpc_id
  subnet_ids               = var.subnet_ids
  control_plane_subnet_ids = var.control_plane_subnet_ids

  eks_managed_node_groups = {
    api_pool = {
      min_size     = 2
      max_size     = 10
      desired_size = 2
      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
      labels = {
        role = "api"
      }
    }
    worker_pool = {
      min_size     = 2
      max_size     = 10
      desired_size = 2
      instance_types = ["t3.large"]
      capacity_type  = "ON_DEMAND"
      labels = {
        role = "worker"
      }
    }
    gpu_pool_t4 = {
      min_size     = 0
      max_size     = 5
      desired_size = 0
      instance_types = ["g4dn.xlarge"]
      capacity_type  = "SPOT"
      labels = {
        role = "gpu-worker"
        gpu_class = "t4"
      }
      taints = [
        {
          key    = "nvidia.com/gpu"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      ]
    }
    gpu_pool_a10g = {
      min_size     = 0
      max_size     = 3
      desired_size = 0
      instance_types = ["g5.2xlarge"]
      capacity_type  = "SPOT"
      labels = {
        role = "gpu-worker"
        gpu_class = "a10g"
      }
      taints = [
        {
          key    = "nvidia.com/gpu"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      ]
    }
    gpu_pool_warm = {
      min_size     = 1
      max_size     = 1
      desired_size = 1
      instance_types = ["g4dn.xlarge"]
      capacity_type  = "ON_DEMAND"
      labels = {
        role = "gpu-worker"
        gpu_class = "t4"
        lifecycle = "warm"
      }
      taints = [
        {
          key    = "nvidia.com/gpu"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      ]
    }
    sandbox_pool = {
      min_size     = 2
      max_size     = 20
      desired_size = 2
      instance_types = ["c5.large"] # Compute optimized for gVisor/Firecracker overhead
      labels = {
        role = "sandbox"
      }
      taints = [
        {
          key    = "sandbox.papertoprod.com/isolated"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      ]
    }
  }

  tags = var.tags
}
