# infra/terraform/modules/iam/main.tf
module "api_irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name = "papertoprod-api-role"

  oidc_providers = {
    main = {
      provider_arn               = var.oidc_provider_arn
      namespace_service_accounts = ["default:api-sa"]
    }
  }

  role_policy_arns = {
    # Least privilege policies
    s3_access      = aws_iam_policy.api_s3.arn
    secrets_access = aws_iam_policy.api_secrets.arn
  }
}

resource "aws_iam_policy" "api_s3" {
  name        = "PaperToProdAPIS3Access"
  description = "Allow API to read/write specific buckets"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:PutObject", "s3:GetObject"]
        Effect   = "Allow"
        Resource = ["arn:aws:s3:::${var.bucket_name}/*"]
      }
    ]
  })
}

resource "aws_iam_policy" "api_secrets" {
  name        = "PaperToProdAPISecretsAccess"
  description = "Allow API to read DB and API keys from Secrets Manager"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["secretsmanager:GetSecretValue"]
        Effect   = "Allow"
        Resource = [var.db_secret_arn, var.stripe_secret_arn]
      }
    ]
  })
}
