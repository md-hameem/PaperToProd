# PaperToProd — Operational Incident Runbooks

## Severity Tiers & Escalation
- **SEV-1 (Critical):** Core pipeline down, data loss, or active security breach. Page primary on-call immediately. (Response SLA: 15m)
- **SEV-2 (Major):** Degradation in service (e.g. queue processing delayed > 1hr). Page primary on-call. (Response SLA: 1h)
- **SEV-3 (Minor):** Individual job failures, minor UI bugs. Log ticket for business hours. (Response SLA: 1d)

---

## Runbook: GPU Pool Saturation (Alert: `GPUPoolSaturated`)
**Symptom:** Grafana alert fires indicating `gpu_pool` node group is at 100% capacity and Celery queue depth is spiking.
**Action:**
1. Check EKS cluster autoscaler logs to ensure AWS quotas are not exceeded.
2. If quotas are hit, gracefully degrade service: Disable complex E2E tests in the Reviewer node via LaunchDarkly feature flag `enable_full_gpu_tests`.
3. Request AWS limit increase for `p4d.24xlarge` instances.

## Runbook: Repair-Loop Spikes (Alert: `ReviewerInfiniteLoop`)
**Symptom:** LLM enters hallucination state, causing the Reviewer agent to fail and retry the maximum 3 times across a high percentage of jobs.
**Action:**
1. Check Anthropic API status for degradation.
2. Inspect the latest `scaffolder` and `reviewer` traces in DataDog to identify prompt shifts.
3. If caused by a bad deployment, rollback the `worker` component using Argo Rollouts: `kubectl argo rollouts undo papertoprod-worker`.

## Runbook: LLM Provider Outage
**Symptom:** High rate of 500/503 errors from Anthropic API.
**Action:**
1. Toggle the environment variable `DEFAULT_LLM_PROVIDER="openai"` in the `worker` configmap to immediately failover to `gpt-4o`.
2. Monitor Fidelity Score dashboard, as failover may slightly impact generation quality.

## Runbook: Sandbox Security Incident (Alert: `SandboxEgressViolation`)
**Symptom:** `sandbox-svc` attempts to connect to internal AWS metadata service or internal VPC IP ranges (caught by NetworkPolicy).
**Action:**
1. **SEV-1 Escalation.**
2. Immediately cordon the node: `kubectl cordon <node-name>`.
3. Terminate the active job via database: `UPDATE jobs SET status = 'failed' WHERE id = <id>;`.
4. Preserve the pod for forensic analysis if possible, otherwise terminate it.
5. Review the user's uploaded paper for prompt injection signatures.
