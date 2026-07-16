# Infrastructure — Terraform

AWS infrastructure definitions for PaperToProd.

## Modules
- `modules/eks-node-pool` — Kubernetes node pool configs (api, worker, gpu, sandbox)
- `modules/rds-postgres` — Managed PostgreSQL
- `modules/elasticache` — Managed Redis
- `modules/s3` — Object storage buckets

## Environments
- `environments/dev/`
- `environments/staging/`
- `environments/prod/`

See Doc 11 for full infrastructure specification.
