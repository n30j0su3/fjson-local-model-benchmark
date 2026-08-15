# Security policy

## Report a vulnerability

Do not open a public issue for vulnerabilities involving secret exposure, path traversal, sandbox escape, network bypass or command injection. Report privately through the repository's GitHub Security Advisory interface.

## Security boundaries

- Generated HTML is untrusted and must pass static plus isolated browser QA.
- Public packs are allowlist-based; raw model responses are local-only.
- n8n is a thin wrapper and never stores benchmark secrets or shell logic.
- Provider credentials belong in environment variables or an external secret manager.

Supported security fixes target the latest release.
