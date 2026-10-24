"""Abstract base provider for inference models."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ProviderStatus(BaseModel):
    name: str
    is_remote: bool
    is_connected: bool
    details: str
    discovered_model: Optional[str] = None


class BaseInferenceProvider(ABC):
    """Abstract interface for all model providers in NEXUS."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_remote(self) -> bool:
        pass

    @abstractmethod
    def check_health(self) -> ProviderStatus:
        """Checks provider connection/reachability safely with short timeouts."""
        pass

    @abstractmethod
    def analyze_plan(self, prompt: str) -> Dict[str, Any]:
        """Submits prompt for analysis, returning validated structured dictionary."""
        pass
