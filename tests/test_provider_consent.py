import pytest
from nexus.providers.gemini import GeminiProvider
from nexus.security.redaction import redact_secrets


def test_gemini_key_enforcement():
    # Without valid API key, invocation must fail closed
    provider = GeminiProvider(api_key="")
    with pytest.raises(ValueError, match="Gemini API key missing"):
        provider.analyze_plan("Analyze this plan")


def test_secret_redaction():
    text_with_keys = "My key is AIzaSyD3x4ampleKey012345678901234567890 and sk-abcdef12345678901234567890"
    sanitized = redact_secrets(text_with_keys)
    assert "AIzaSy" not in sanitized
    assert "sk-" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized
