"""Local Gemma provider interfacing strictly with validated loopback llama.cpp / OpenAI-compatible servers."""

from typing import Dict, Any, Optional
import httpx
from nexus.providers.base import BaseInferenceProvider, ProviderStatus
from nexus.config import DEFAULT_LOOPBACK_ENDPOINT, DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT
from nexus.security.endpoint_policy import validate_loopback_endpoint


class LocalGemmaProvider(BaseInferenceProvider):
    """
    Connects strictly to an explicitly validated loopback llama-server endpoint.
    Egress to external networks is rejected by endpoint policy.
    Redirects are disabled to prevent SSRF rebound attacks.
    """

    def __init__(self, endpoint: str = DEFAULT_LOOPBACK_ENDPOINT):
        self.endpoint = validate_loopback_endpoint(endpoint)

    @property
    def name(self) -> str:
        return "Local Gemma (Loopback Engine)"

    @property
    def is_remote(self) -> bool:
        return False

    def check_health(self) -> ProviderStatus:
        models_url = f"{self.endpoint.rstrip('/')}/models"
        health_url = "http://127.0.0.1:8080/health"
        models_url = f"{self.endpoint.rstrip('/')}/models"
        try:
            with httpx.Client(timeout=DEFAULT_CONNECT_TIMEOUT, follow_redirects=False) as client:
                # 1. Check health endpoint
                try:
                    h_resp = client.get(health_url)
                    if h_resp.status_code == 503:
                        return ProviderStatus(
                            name=self.name,
                            is_remote=False,
                            is_connected=False,
                            details="Model is currently loading into memory...",
                        )
                except Exception:
                    pass

                resp = client.get(models_url)
                if resp.status_code == 200:
                    data = resp.json()
                    model_id = "gemma-4-e2b"
                    if isinstance(data, dict) and "data" in data and len(data["data"]) > 0:
                        model_id = data["data"][0].get("id", model_id)
                        # Extract basename if path
                        if "\\" in model_id or "/" in model_id:
                            model_id = model_id.replace("\\", "/").split("/")[-1]
                    return ProviderStatus(
                        name=self.name,
                        is_remote=False,
                        is_connected=True,
                        details="Local server active and reachable on loopback.",
                        discovered_model=model_id,
                    )
                return ProviderStatus(
                    name=self.name,
                    is_remote=False,
                    is_connected=False,
                    details=f"Server returned HTTP status {resp.status_code} at {models_url}",
                )
        except Exception as e:
            return ProviderStatus(
                name=self.name,
                is_remote=False,
                is_connected=False,
                details=f"Offline / Disconnected: Could not reach {self.endpoint} ({type(e).__name__})",
            )

    def analyze_plan(self, prompt: str) -> Dict[str, Any]:
        chat_url = f"{self.endpoint.rstrip('/')}/chat/completions"
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are NEXUS AI Failure Analyzer. Return clear, concise findings.",
                },
                {"role": "user", "content": prompt[:4000]},
            ],
            "temperature": 0.1,
            "max_tokens": 512,
        }
        with httpx.Client(timeout=120.0, follow_redirects=False) as client:
            resp = client.post(chat_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # If thinking model puts output in reasoning_content, handle gracefully
            choices = data.get("choices", [{}])
            if choices:
                msg = choices[0].get("message", {})
                if not msg.get("content") and msg.get("reasoning_content"):
                    msg["content"] = msg.get("reasoning_content")
            return data
