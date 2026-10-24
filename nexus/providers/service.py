"""Unified AI Provider Service coordinating Local Gemma and Gemini API with persistence."""

from typing import Dict, Any, Optional
from nexus.providers.base import BaseInferenceProvider, ProviderStatus
from nexus.providers.local_gemma import LocalGemmaProvider
from nexus.providers.gemini import GeminiProvider
from nexus.storage.db import NexusDatabase


class AIProviderService:
    """
    Centralized inference router:
    - Supports 'local_gemma' and 'gemini'
    - Persists active provider choice in SQLite settings
    - NEVER silently falls back
    - Returns standardized inference dictionaries
    """

    def __init__(self, db: Optional[NexusDatabase] = None):
        self.db = db or NexusDatabase()
        self.local_provider = LocalGemmaProvider()
        self.gemini_provider = GeminiProvider()

    def get_active_provider_name(self) -> str:
        """Returns 'local_gemma' or 'gemini'. Defaults to 'local_gemma'."""
        saved = self.db.get_setting("active_ai_provider", "local_gemma")
        return saved if saved in ("local_gemma", "gemini") else "local_gemma"

    def set_active_provider(self, provider_name: str) -> str:
        """Sets and persists active provider."""
        if provider_name not in ("local_gemma", "gemini"):
            raise ValueError(f"Unsupported provider: '{provider_name}'. Must be 'local_gemma' or 'gemini'.")
        self.db.set_setting("active_ai_provider", provider_name)
        return provider_name

    def get_active_provider(self) -> BaseInferenceProvider:
        """Returns the instance of the active provider."""
        active = self.get_active_provider_name()
        if active == "gemini":
            return self.gemini_provider
        return self.local_provider

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive diagnostic status for both providers and active selection."""
        active_name = self.get_active_provider_name()
        local_health = self.local_provider.check_health()
        gemini_health = self.gemini_provider.check_health()

        return {
            "active_provider": active_name,
            "local_gemma": local_health.model_dump(),
            "gemini": gemini_health.model_dump(),
        }

    def chat_or_analyze(self, prompt: str) -> Dict[str, Any]:
        """
        Routes prompt to active provider.
        Raises descriptive error on failure without silent fallback.
        """
        active_name = self.get_active_provider_name()
        provider = self.get_active_provider()
        health = provider.check_health()

        if not health.is_connected:
            if active_name == "gemini":
                raise RuntimeError(
                    f"Gemini API unavailable: {health.details}. Ensure GEMINI_API_KEY is configured in .env."
                )
            else:
                raise RuntimeError(
                    f"Local Gemma server unavailable: {health.details}. Run start_local_model.bat."
                )

        return provider.analyze_plan(prompt)
