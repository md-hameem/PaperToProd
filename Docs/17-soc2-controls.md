# PaperToProd SOC 2 Type II Controls Matrix

This document outlines the formalized technical and organizational controls implemented within PaperToProd to satisfy the AICPA Trust Services Criteria (Security, Availability, Confidentiality).

## 1. Security (Logical and Physical Access) - CC6

### CC6.1 - Logical Access Security
- **Authentication**: All API requests require a valid JWT (issued via Google OAuth 2.0) or an explicit API Key.
- **Authorization (RBAC)**: Workspaces enforce strictly segregated Role-Based Access Control (Owner, Admin, Member). All API endpoints modifying workspace assets are protected by `require_workspace_role()`.
- **Principle of Least Privilege**: IAM roles in AWS are strictly scoped (e.g. S3 replication roles only permit `GetObjectVersion` and `ReplicateObject` on designated buckets).

## 2. Security (System Operations) - CC7

### CC7.1 - Configuration and Vulnerability Management
- **Audit Logging**: A centralized `structlog` middleware intercepts and logs all state-mutating requests (POST, PUT, PATCH, DELETE) as `[AUDIT]` events, capturing the authenticated `actor_id` (JWT `sub` or API Key hash), request ID, timestamp, and HTTP method.
- **Tracing**: OpenTelemetry provides end-to-end distributed tracing across the API and Celery workers.
- **Secrets Management**: Sensitive credentials (e.g., BYO LLM API Keys) are encrypted at rest using `cryptography.fernet` AES-128-CBC/HMAC envelope encryption. Raw keys are never stored in plain text or emitted in API responses.

## 3. Security (Change Management) - CC8

### CC8.1 - Authorization and Testing
- **Version Control**: All infrastructure and application changes are managed in Git.
- **Testing**: Pre-commit hooks (Ruff, Mypy) and automated unit tests are enforced. Changes must pass CI checks before being merged.
- **Infrastructure as Code**: All environments (prod, prod-dr) are defined deterministically in Terraform, requiring explicit plan reviews before applying.

## 4. Availability - A1

### A1.1 - Processing Capacity and DR
- **Disaster Recovery (DR)**: A warm-standby environment is configured in `us-west-2` via Terraform.
- **Data Redundancy**:
  - Cross-Region Replication (CRR) is enabled on critical S3 buckets (job artifacts, papers).
  - Cross-Region Read Replicas are configured for the primary PostgreSQL RDS database, supporting an RPO of ≤ 5 minutes.
- **RTO/RPO Targets**: RPO ≤ 5 minutes, RTO ≤ 1 hour for the core API and worker pool.

## 5. Confidentiality - C1

### C1.1 - Data Protection
- **Encryption at Rest**: PostgreSQL (RDS) and S3 buckets are encrypted using AWS KMS.
- **Encryption in Transit**: All API traffic is secured via TLS 1.3. Internal service-to-service communication relies on encrypted channels or VPC private networking.
- **Tenant Isolation**: Data is logically isolated via `workspace_id` scoping on all database queries. BYO LLM Keys ensure Enterprise tenants can route raw prompts through their own directly-billed LLM providers, completely bypassing PaperToProd's central accounts.
