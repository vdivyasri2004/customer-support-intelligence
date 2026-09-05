from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class AIProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def summarize_ticket(self, subject: str, description: str, category: str, priority: str) -> str:
        pass

    @abstractmethod
    def generate_insights(self, analytics_data: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def answer_question(self, question: str, analytics_context: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def generate_recommendations(self, analytics_data: Dict[str, Any]) -> List[str]:
        pass


class UnavailableAIProvider(AIProvider):
    def is_available(self) -> bool:
        return False

    def summarize_ticket(self, subject: str, description: str, category: str, priority: str) -> str:
        return "AI summary unavailable. Please configure an AI provider."

    def generate_insights(self, analytics_data: Dict[str, Any]) -> str:
        return "AI insights unavailable. Please configure an AI provider."

    def answer_question(self, question: str, analytics_context: Dict[str, Any]) -> str:
        return "AI Q&A unavailable. Please configure an AI provider."

    def generate_recommendations(self, analytics_data: Dict[str, Any]) -> List[str]:
        return ["AI recommendations unavailable. Please configure an AI provider."]
