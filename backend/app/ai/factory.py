from functools import lru_cache

from app.ai.base import AIService
from app.ai.llm import LLMAIService
from app.ai.mock import MockAIService
from app.config import get_settings


@lru_cache
def get_ai_service() -> AIService:
    settings = get_settings()
    if settings.use_mock_ai:
        return MockAIService()
    return LLMAIService()
