module "s3_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 3.0"

  bucket = var.bucket_name
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  versioning = {
    enabled = true
  }

  replication_configuration = var.replication_enabled ? {
    role = aws_iam_role.replication[0].arn
    rules = [
      {
        id     = "dr-replication"
        status = "Enabled"
        destination = {
          bucket = var.replication_destination_bucket_arn
        }
      }
    ]
  } : {}

  tags = var.tags
}

resource "aws_iam_role" "replication" {
  count = var.replication_enabled ? 1 : 0
  name  = "${var.bucket_name}-s3-replication-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "replication" {
  count = var.replication_enabled ? 1 : 0
  name  = "${var.bucket_name}-s3-replication-policy"
  role  = aws_iam_role.replication[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          module.s3_bucket.s3_bucket_arn
        ]
      },
      {
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Effect = "Allow"
        Resource = [
          "${module.s3_bucket.s3_bucket_arn}/*"
        ]
      },
      {
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Effect = "Allow"
        Resource = [
          "${var.replication_destination_bucket_arn}/*"
        ]
      }
    ]
  })
}
