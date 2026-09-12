from abc import ABC, abstractmethod
from typing import Any


class AIService(ABC):
    """Production-planning assistant. Never auto-assigns work."""

    @abstractmethod
    def estimate_schedule(self, context: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def detect_bottlenecks(self, context: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def recommend_artist(self, context: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def calculate_risk(self, context: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def answer_project_question(self, question: str, context: dict[str, Any]) -> dict[str, Any]: ...
