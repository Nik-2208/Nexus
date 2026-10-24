"""Demo provider returning deterministic app-authored fixtures with zero network calls."""

from typing import Dict, Any
from nexus.providers.base import BaseInferenceProvider, ProviderStatus


class DemoProvider(BaseInferenceProvider):
    """
    100% offline deterministic provider.
    Never makes network calls, requires no API keys, and has zero external dependencies.
    """

    @property
    def name(self) -> str:
        return "Demo Mode (Deterministic Fixture)"

    @property
    def is_remote(self) -> bool:
        return False

    def check_health(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            is_remote=False,
            is_connected=True,
            details="Operational (Zero network activity, deterministic offline fixtures)",
            discovered_model="built-in-deterministic-engine",
        )

    def analyze_plan(self, prompt: str) -> Dict[str, Any]:
        return {
            "mode": "demo_deterministic",
            "provider": self.name,
            "provenance": "deterministic_rule",
            "findings_count": 4,
            "status": "success",
        }
