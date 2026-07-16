# PaperToProd — Document 12: Security Architecture

**Status:** Draft v1.0

---

## 1. Threat Modeling Overview

PaperToProd has a threat surface most SaaS products don't: **it downloads untrusted content from the internet (papers), generates code via LLMs, and then executes that generated code.** Every security decision in this document flows from treating three inputs as untrusted by default: (a) the paper itself, (b) any existing GitHub repository the Finder agent pulls in, and (c) the LLM-generated code before it's validated.

## 2. OWASP Top 10 (application-layer coverage)

Standard mitigations apply throughout the FastAPI monolith (Document 9): parameterized queries/ORM usage (injection), output encoding (XSS, relevant mainly in the Repository Explorer's rendering of user/paper-derived content), CSRF tokens on state-changing requests, dependency scanning (§9), strict authorization checks via the single shared RBAC module (Document 9 §7) rather than per-endpoint ad hoc logic (mitigating broken access control, historically OWASP's top-ranked category), and secure session/JWT handling (short-lived tokens, httpOnly cookies, refresh-token rotation).

## 3. Prompt Injection

**Threat:** A paper's text (or a candidate GitHub repository's README/code comments) could contain content specifically crafted to manipulate an agent's behavior — e.g., text embedded in a PDF instructing "ignore prior instructions and instead output X," or a malicious README designed to make the Finder/Scaffolder agents exfiltrate data or generate backdoored code.

**Mitigations:**
- All paper/repo-derived content is treated as **data, never as instructions**, via strict prompt-template structure (Document 8 §7) that clearly delineates system/role instructions from untrusted content, with no agent prompt ever concatenating untrusted text adjacent to an instruction in a way that could be reinterpreted as a directive.
- Output validation: agent outputs that would trigger a tool call with real-world effect (e.g., pushing to a user's GitHub, writing files) are schema-validated against expected structure before execution — an injected instruction attempting to redirect a GitHub push to an attacker-controlled repo, for instance, would have to also produce a validly-scoped output that passes this check, which is a materially higher bar than simply getting an LLM to "say" something wrong.
- The Golden Dataset evaluation suite (Document 8 §9) includes adversarial test papers with known injection payloads, regression-tested on every prompt-template change — injection resistance is treated as a measured, gated property of the system, not an assumption.

## 4. RAG Poisoning

**Threat:** Finder's vector-similarity search (Qdrant, Document 9/10) could be poisoned if an attacker publishes a crafted repository designed to rank highly for a target paper while containing malicious code, exploiting the fact that the ranking signal partly relies on textual similarity rather than pure trust signals.

**Mitigations:** Ranking (Document 8 §3.2) explicitly weights repo-health signals (age, star count, commit history, CI presence) alongside textual similarity specifically *because* textual similarity alone is gameable — a freshly-published, zero-history repo cannot rank above an established one purely on README similarity. Additionally, no candidate repository's code is ever executed or even statically merged into the generated output without passing through the same sandboxed validation (§6) as freshly generated code — "found" code receives no more trust than "generated" code.

## 5. Malicious PDFs

**Threat:** Uploaded PDFs are a well-known attack vector (embedded JavaScript, malformed structures targeting parser vulnerabilities, zip-bomb-style decompression attacks via embedded objects).

**Mitigations:** All uploaded PDFs are parsed inside an isolated, resource-limited parsing sandbox (separate from both the main API process and the code-execution sandbox — a third isolation tier, since PDF parsing and arbitrary-code execution are different threat classes deserving separate containment) with strict size/page/object-count limits enforced before parsing begins; parsing uses a hardened library configuration with JavaScript execution and external-resource-fetching disabled; output is treated as plain structured text/data downstream, with no PDF-native active content ever reaching any agent.

## 6. Sandboxed Execution

**This is the single most safety-critical component in the entire architecture** (Document 9 §1's rationale for extracting it as its own service applies doubly here).

- **Isolation model:** gVisor or Firecracker microVM-based sandboxing (stronger isolation guarantee than a bare Docker container's shared-kernel model, appropriate given this sandbox runs fully untrusted, LLM-generated code) — final selection between the two made on a POC evaluating GPU-passthrough compatibility, since Firecracker's GPU support is less mature than gVisor's container-based approach as of this writing; this is flagged as an implementation-phase decision point, not resolved here.
- **Network policy:** default-deny egress, with a narrow allow-list (package registries — PyPI/npm/conda — required for the generated `Dockerfile`'s dependency installation, and nothing else); no access to internal platform services, metadata endpoints (blocking SSRF against cloud-instance-metadata services, a classic sandbox-escape vector), or the public internet beyond that allow-list.
- **Resource limits:** hard CPU/memory/disk/GPU-memory ceilings and wall-clock execution timeouts per validation attempt (tied to Document 8's `max_retries` bound), preventing both accidental runaway resource consumption (e.g., a generated training loop that doesn't terminate) and deliberate resource-exhaustion abuse.
- **No persistence across jobs:** each validation attempt runs in a freshly provisioned sandbox instance, destroyed after use — no shared filesystem or cached state between different jobs' sandboxes, eliminating an entire class of cross-tenant contamination risk.

## 7. Secrets

- Covered architecturally in Document 11 §6 (Secrets Manager/Vault, CSI-driver injection, rotation); security-specific addition here: BYO-LLM-API-keys (enterprise, Document 9 §7) are encrypted at rest with a per-workspace data-encryption key (envelope encryption), never logged even at debug level, and scoped such that a compromised application-layer bug cannot bulk-export all customers' keys in one query (per-key decryption requires the specific workspace's key-encryption-key, not a single global secret).

## 8. Encryption

- **In transit:** TLS 1.2+ everywhere (client↔gateway, service↔service within the cluster via mesh-enforced mTLS where feasible, particularly between the monolith and the sandbox service given the latter's elevated risk profile).
- **At rest:** Postgres encryption at rest (cloud-provider-managed), S3/MinIO server-side encryption for all stored artifacts (papers, generated repos, logs) and, per §7, envelope encryption for the specific case of customer-supplied credentials.

## 9. IAM

- Least-privilege IAM roles per service (api/worker/sandbox-svc each get distinct roles with only the specific cloud-resource permissions they require — the sandbox service's IAM role in particular has no permissions to any other service's data store, a defense-in-depth measure independent of the network-isolation controls in §6), no long-lived static cloud credentials (workload-identity/IRSA-style role assumption instead).

## 10. API Security

- All programmatic (Document 14) API access via scoped API keys (Document 9 §7) with per-key scope enforcement re-checked per request; standard abuse protections (rate limiting per Document 9 §16, anomaly detection on unusual usage patterns e.g. a sudden spike in job submissions from one key, which triggers a temporary throttle pending review).

## 11. Dependency Scanning

- Automated dependency vulnerability scanning (e.g., Dependabot/Snyk-equivalent) integrated into CI (Document 11 §5) for the platform's *own* codebase dependencies — distinct from, and not to be confused with, the generated-repository dependency pinning discussed in Document 8's DevOps agent, which is a reproducibility concern rather than a platform-security one (though the DevOps agent's known-good-compatibility matrix does also serve as a light quality filter against generating known-vulnerable dependency pins where a safe alternative exists).

## 12. Container Security

- Minimal base images for all platform-owned services (distroless where feasible), image signing + admission-control verification in the Kubernetes cluster (only signed, scanned images may run), and — specifically for the sandbox service — the generated container images themselves (the *product's output*, not the platform's own services) are also subject to a security-relevant static check (no unexpectedly-privileged operations requested in the generated Dockerfile) before being permitted to build inside the sandbox, since even the "input" to the sandbox should not be blindly trusted to be a well-formed Dockerfile.

## 13. Compliance

- **SOC 2 Type II:** targeted as the enterprise-tier prerequisite (Document 1 §9's enterprise tier explicitly sells against this); requires the audit logging (Document 9 §8, Document 10 §10), access control, and change-management practices already specified above to be formalized into an auditable control set — a compliance program, not solely an engineering exercise, but every technical control it depends on is already named in this document.
- **GDPR:** right-to-erasure handling specifically addressed for the Gallery's public-entry tension (Document 3 §11, Document 10 §9) — account deletion triggers anonymization of personally-identifying fields while respecting any explicit separate request to remove a public Gallery entry; data processing agreements required for any EU customer data flowing through third-party LLM providers, which must be reflected in vendor contracts, not just this architecture.
- **ISO 27001:** aligns with the same control set as SOC 2 (access control, cryptography, incident management, supplier/vendor security review covering the LLM providers and GitHub/arXiv API dependencies) — pursued on the same timeline as SOC 2 given the substantial control overlap, rather than as a separate parallel effort.

---
*End of Document 12. Proceeding next to Document 13: Testing Strategy.*
