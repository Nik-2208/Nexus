"""Secret redaction and output sanitization helpers."""

import re

# Patterns matching sensitive keys/tokens
API_KEY_PATTERNS = [
    re.compile(r"AIzaSy[0-9A-Za-z_-]{33}"),  # Google/Gemini API key format
    re.compile(r"sk-[0-9a-zA-Z]{20,}"),      # OpenAI/standard secret key format
    re.compile(r"(?i)(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{8,})['\"]?"),
]


def redact_secrets(text: str) -> str:
    """
    Scans text and redacts recognized API keys and credentials with [REDACTED].
    Ensures secrets never leak into UI, logs, errors, or persistent storage.
    """
    if not text or not isinstance(text, str):
        return text

    sanitized = text
    for pattern in API_KEY_PATTERNS:
        # Match groups if available or full match
        def _repl(match):
            if len(match.groups()) >= 2:
                # Key-value match: keep label, redact secret value
                label = match.group(1)
                return f"{label}: [REDACTED_SECRET]"
            return "[REDACTED_SECRET]"

        sanitized = pattern.sub(_repl, sanitized)

    return sanitized


def sanitize_for_plain_display(text: str) -> str:
    """
    Prepares text for safe, inert UI display without HTML interpretation.
    Strips raw HTML tags or script injection attempts.
    """
    if not text or not isinstance(text, str):
        return ""
    # Strip script tags and brackets
    cleaned = re.sub(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "[SCRIPTR_REMOVED]", text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = cleaned.replace("<", "&lt;").replace(">", "&gt;")
    return redact_secrets(cleaned)
