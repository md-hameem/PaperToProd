# Enterprise Deployment Guide

This guide details how to deploy PaperToProd into an isolated, self-hosted Enterprise environment (e.g., an AWS VPC with peered connectivity to your corporate network).

## Architecture Overview

Enterprise deployments are designed to minimize internet exposure and utilize your existing, managed data stores.
Instead of the standard PaperToProd Helm charts provisioning PostgreSQL and Redis, you will provide the connection strings to your own managed instances.

The EKS cluster will be provisioned with `endpoint_public_access = false`, meaning the Kubernetes API is only accessible from within the peered VPC.

## Prerequisites

1. **Corporate Network**: An existing AWS VPC or on-premise network connected via Direct Connect/Transit Gateway.
2. **PostgreSQL**: A PostgreSQL 15+ cluster accessible from the peered VPC.
3. **Redis**: A Redis 7+ cluster accessible from the peered VPC.
4. **Object Storage**: An S3-compatible API (e.g., AWS S3 with VPC Endpoints, or self-hosted MinIO).

## 1. Infrastructure Provisioning (Terraform)

Use the provided Terraform enterprise environment module to provision the EKS cluster and VPC peering:

```bash
cd infra/terraform/environments/enterprise
terraform init
terraform apply -var="customer_name=YourCorp" -var="corporate_vpc_id=vpc-0123456789abcdef0"
```

This provisions `papertoprod-enterprise-vpc` and peers it to `vpc-0123456789abcdef0`.

## 2. Helm Chart Configuration

Create your own `values-enterprise-overrides.yaml` based on the provided `values-enterprise.yaml` template:

```yaml
# values-enterprise-overrides.yaml
externalDatabase:
  url: "postgresql://papertoprod:SuperSecret123@your-corporate-db.internal:5432/papertoprod"

externalRedis:
  url: "redis://:RedisSecret123@your-corporate-redis.internal:6379/0"

externalS3:
  endpoint: "https://minio.your-corp.internal:9000"
  accessKey: "your-access-key"
  secretKey: "your-secret-key"
```

## 3. Deployment

Install the Helm charts into the private EKS cluster:

```bash
# Ensure your kubeconfig is configured for the private cluster
aws eks update-kubeconfig --name papertoprod-enterprise-cluster --region us-east-1

helm upgrade --install papertoprod-api ./infra/helm/api -f ./infra/helm/api/values-enterprise.yaml -f values-enterprise-overrides.yaml
helm upgrade --install papertoprod-worker ./infra/helm/worker -f ./infra/helm/worker/values-enterprise.yaml -f values-enterprise-overrides.yaml
```

## 4. Single Sign-On (SSO)

Enterprise SSO (SAML/OIDC) configuration is handled via environment variables passed to the API.
*(Note: Full SSO integration setup is detailed in the upcoming Phase 4.3 release notes).*
