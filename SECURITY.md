# SECURITY POLICY & POSTURE — NEXUS

## Threat Model Summary
NEXUS analyzes AI agent plans and textual artifacts that may contain hostile instructions, prompt injection attempts, or adversarial code snippets.
Application-level boundaries isolate untrusted inputs:
1. **Input Boundaries:** Inputs are parsed strictly as passive textual data.
2. **Process Boundaries:** Model output cannot invoke shell commands, file modifications, or process spawning.
3. **Network Isolation:** Local inference is restricted exclusively to loopback endpoints.
4. **Data Privacy:** Local SQLite storage is stored locally under `nexus_data/`. Unencrypted at rest (standard OS filesystem permissions apply).

## Security Invariants Enforced
- **Zero Silent Egress:** Remote APIs are strictly opt-in with explicit user confirmation.
- **SSRF Prevention:** Reject all non-loopback addresses, redirects, and userinfo in URLs.
- **Secret Redaction:** Auto-redact API key patterns matching Google and standard tokens.
- **Strict Bounding:** Input lengths, graph node/edge counts, and recursion depths are strictly limited.

## Vulnerability Reporting
To report security vulnerabilities, open a private security advisory through the repository's verified GitHub channel or contact maintainers directly.
