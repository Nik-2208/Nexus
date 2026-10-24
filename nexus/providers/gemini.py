"""Gemini remote provider using official Google GenAI SDK and secure .env loading."""

from typing import Dict, Any, Optional
import google.generativeai as genai
from nexus.providers.base import BaseInferenceProvider, ProviderStatus
from nexus.security.redaction import redact_secrets
from nexus.config import GEMINI_API_KEY, GEMINI_MODEL


class GeminiProvider(BaseInferenceProvider):
    """
    Official Gemini provider interfacing via Google Generative AI SDK.
    Requires GEMINI_API_KEY to be set in environment (.env).
    Returns strict, standard OpenAI-compatible choices format for seamless provider switching.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self._api_key = (api_key or GEMINI_API_KEY).strip()
        self._model_name = (model_name or GEMINI_MODEL or "gemini-1.5-flash").strip()

    @property
    def name(self) -> str:
        return "Gemini API"

    @property
    def is_remote(self) -> bool:
        return True

    def check_health(self) -> ProviderStatus:
        if not self._api_key or self._api_key == "your_gemini_api_key_here":
            return ProviderStatus(
                name=self.name,
                is_remote=True,
                is_connected=False,
                details="GEMINI_API_KEY is not set or contains placeholder in .env.",
            )
        try:
            genai.configure(api_key=self._api_key)
            # Lightweight verification: list models or retrieve model metadata
            model_info = genai.get_model(f"models/{self._model_name}")
            return ProviderStatus(
                name=self.name,
                is_remote=True,
                is_connected=True,
                details=f"Ready ({self._model_name})",
                discovered_model=self._model_name,
            )
        except Exception as e:
            err_msg = str(e)
            if "API_KEY_INVALID" in err_msg or "400" in err_msg:
                details = "Invalid GEMINI_API_KEY provided."
            else:
                details = f"Gemini connection error: {err_msg[:80]}"
            return ProviderStatus(
                name=self.name,
                is_remote=True,
                is_connected=False,
                details=details,
            )

    def analyze_plan(self, prompt: str) -> Dict[str, Any]:
        if not self._api_key or self._api_key == "your_gemini_api_key_here":
            raise ValueError(
                "Gemini API key missing. Configure GEMINI_API_KEY in .env to use Gemini API."
            )

        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(self._model_name)

        sanitized_prompt = redact_secrets(prompt[:8000])
        response = model.generate_content(sanitized_prompt)
        text_content = response.text if response and hasattr(response, "text") else ""

        # Format into unified OpenAI-compatible choices structure
        return {
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": text_content,
                    },
                }
            ],
            "model": self._model_name,
            "provider": self.name,
            "is_remote": True,
        }
