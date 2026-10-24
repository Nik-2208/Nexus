import pytest
from nexus.security.endpoint_policy import validate_loopback_endpoint, validate_gemini_endpoint, SSRFPolicyViolationError


def test_loopback_policy_allows_valid_loopback():
    assert validate_loopback_endpoint("http://127.0.0.1:8080/v1") == "http://127.0.0.1:8080/v1"
    assert validate_loopback_endpoint("http://localhost:8080") == "http://localhost:8080"


def test_loopback_policy_rejects_ssrf_and_remote():
    with pytest.raises(SSRFPolicyViolationError):
        validate_loopback_endpoint("http://169.254.169.254/latest/meta-data")

    with pytest.raises(SSRFPolicyViolationError):
        validate_loopback_endpoint("http://attacker.com/v1")

    with pytest.raises(SSRFPolicyViolationError):
        validate_loopback_endpoint("http://user:pass@127.0.0.1:8080")

    with pytest.raises(SSRFPolicyViolationError):
        validate_loopback_endpoint("http://127.0.0.1\\@attacker.com")


def test_gemini_endpoint_policy():
    assert validate_gemini_endpoint("https://generativelanguage.googleapis.com/v1beta")
    with pytest.raises(SSRFPolicyViolationError):
        validate_gemini_endpoint("http://generativelanguage.googleapis.com")  # reject http
    with pytest.raises(SSRFPolicyViolationError):
        validate_gemini_endpoint("https://evil-proxy.com/v1beta")
