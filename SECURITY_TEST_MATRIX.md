# SECURITY TEST MATRIX — NEXUS

| Test ID | Risk Category | Implementation Control | Test File | Verified Status |
|---|---|---|---|---|
| SEC-01 | SSRF / Remote Egress | `validate_loopback_endpoint` checks host & IP loopback flag | `tests/test_endpoint_policy.py` | Verified |
| SEC-02 | Silent Cloud Transmission | `GeminiProvider` blocks calls without explicit consent | `tests/test_provider_consent.py` | Verified |
| SEC-03 | Secret Leaks | `redact_secrets` regex replacement pattern | `tests/test_provider_consent.py` | Verified |
| SEC-04 | Goal Invariant Violation | `analyze_goal_rot` flags cloud dependencies violating offline rule | `tests/test_goal_checks.py` | Verified |
| SEC-05 | Cycle Exhaustion | `calculate_downstream_blast_radius` uses depth-bounded BFS | `tests/test_graph.py` | Verified |
| SEC-06 | Demo Mode Determinism | `DemoProvider` executes without network or API keys | `tests/test_demo_workflow.py` | Verified |
