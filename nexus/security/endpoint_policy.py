"""Network and endpoint validation enforcing loopback-only and strict SSRF prevention."""

import ipaddress
from urllib.parse import urlparse
from nexus.config import ALLOWED_LOOPBACK_HOSTS, OFFICIAL_GEMINI_API_HOST


class SSRFPolicyViolationError(ValueError):
    """Raised when an endpoint violates loopback isolation or destination restrictions."""
    pass


def validate_loopback_endpoint(url: str) -> str:
    """
    Validates that a model endpoint connects ONLY to loopback (127.0.0.1, localhost, [::1]).
    Rejects:
    - Userinfo (credentials in URL)
    - Non-http(s) schemes
    - Remote IPs or non-loopback domain names
    - Backslash / path obfuscations
    """
    if not url or not isinstance(url, str):
        raise SSRFPolicyViolationError("Invalid endpoint URL: empty or non-string.")

    if "\\" in url:
        raise SSRFPolicyViolationError("Invalid endpoint URL: backslash characters forbidden.")

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise SSRFPolicyViolationError(f"Disallowed scheme: '{parsed.scheme}'. Only http/https permitted.")

    if parsed.username or parsed.password:
        raise SSRFPolicyViolationError("Disallowed credentials/userinfo embedded in endpoint URL.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFPolicyViolationError("Missing hostname in endpoint URL.")

    hostname_lower = hostname.lower()

    # Direct match on allowed loopback strings
    if hostname_lower in ALLOWED_LOOPBACK_HOSTS:
        return url

    # IP address evaluation
    try:
        ip = ipaddress.ip_address(hostname_lower)
        if not ip.is_loopback:
            raise SSRFPolicyViolationError(
                f"Destination IP '{hostname}' is not a loopback address. Egress strictly prohibited."
            )
    except ValueError:
        # Not a raw IP and not in allowed loopback hosts
        raise SSRFPolicyViolationError(
            f"Destination host '{hostname}' is not an authorized loopback address."
        )

    return url


def validate_gemini_endpoint(url: str) -> str:
    """
    Validates that Gemini remote endpoint connects strictly to the official HTTPS host.
    """
    if not url:
        raise SSRFPolicyViolationError("Empty Gemini endpoint URL.")
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise SSRFPolicyViolationError("Gemini endpoint requires HTTPS.")
    if parsed.hostname != OFFICIAL_GEMINI_API_HOST:
        raise SSRFPolicyViolationError(
            f"Unauthorized remote Gemini endpoint host '{parsed.hostname}'. Must be '{OFFICIAL_GEMINI_API_HOST}'."
        )
    return url
