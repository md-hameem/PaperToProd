# Apps — Sandbox Service (Isolated Execution)

The most security-critical component — runs untrusted, LLM-generated code in
network-isolated, resource-limited sandboxes (gVisor or Firecracker).

## Security Properties
- Default-deny network egress (allow-list: PyPI, npm, conda only)
- Hard CPU/memory/disk/GPU-memory/wall-clock limits per attempt
- No persistence across jobs (fresh sandbox per attempt)
- No access to platform secrets or other tenants' data
- Separate IAM role with no permissions to other services' data stores

## Structure

```
sandbox-svc/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI service for sandbox execution requests
│   ├── executor.py       # Container build + execution logic
│   └── config.py         # Resource limits, timeouts, network rules
│
├── tests/
│   └── __init__.py
│
├── Dockerfile
└── requirements.txt
```
