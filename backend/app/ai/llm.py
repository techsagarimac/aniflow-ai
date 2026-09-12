from __future__ import annotations

import json
from typing import Any

import httpx

from app.ai.base import AIService
from app.ai.mock import MockAIService
from app.config import get_settings


class LLMAIService(AIService):
    """OpenAI-compatible chat completions. Falls back to mock on failure."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.ai_api_key
        self.model = settings.ai_model
        self.base_url = settings.ai_base_url.rstrip("/")
        self._fallback = MockAIService()

    def _complete(self, system: str, user: str, fallback: dict[str, Any]) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=20) as client:
                res = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "temperature": 0.2,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                    },
                )
                res.raise_for_status()
                content = res.json()["choices"][0]["message"]["content"]
                data = json.loads(content)
                data.setdefault("is_ai_estimate", True)
                return data
        except Exception:
            return fallback

    def estimate_schedule(self, context: dict[str, Any]) -> dict[str, Any]:
        fallback = self._fallback.estimate_schedule(context)
        return self._complete(
            "You are AniFlow AI, a production planning assistant. Return JSON only. Label estimates as AI estimates, never guarantees.",
            json.dumps(context),
            fallback,
        )

    def detect_bottlenecks(self, context: dict[str, Any]) -> dict[str, Any]:
        fallback = self._fallback.detect_bottlenecks(context)
        return self._complete(
            "Detect production bottlenecks. Never auto-reassign work. Recommendations require manager approval. JSON only.",
            json.dumps(context),
            fallback,
        )

    def recommend_artist(self, context: dict[str, Any]) -> dict[str, Any]:
        fallback = self._fallback.recommend_artist(context)
        return self._complete(
            "Recommend an artist. Manager must approve assignment. JSON with recommended and alternatives.",
            json.dumps(context),
            fallback,
        )

    def calculate_risk(self, context: dict[str, Any]) -> dict[str, Any]:
        fallback = self._fallback.calculate_risk(context)
        return self._complete(
            "Calculate a 0-100 production risk score with factors. JSON only.",
            json.dumps(context),
            fallback,
        )

    def answer_project_question(self, question: str, context: dict[str, Any]) -> dict[str, Any]:
        fallback = self._fallback.answer_project_question(question, context)
        return self._complete(
            "Answer using only the provided production database context. You are AniFlow Assistant, not a generic chatbot.",
            json.dumps({"question": question, "context": context}),
            fallback,
        )
