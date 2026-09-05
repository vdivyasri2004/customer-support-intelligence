import json
import httpx
from typing import Optional, Dict, Any, List
from app.ai.provider import AIProvider
from app.core.config import get_settings


class LocalAIProvider(AIProvider):
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.LOCAL_AI_BASE_URL
        self.model = self.settings.LOCAL_AI_MODEL

    def is_available(self) -> bool:
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("models", [])
                if self.model:
                    return any(m.get("name", "").startswith(self.model) for m in models)
                return len(models) > 0
            return False
        except Exception:
            return False

    def _call(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        try:
            payload = {
                "model": self.model or "llama3.2",
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens},
            }
            resp = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=60.0)
            if resp.status_code == 200:
                return resp.json().get("response", "")
            return None
        except Exception:
            return None

    def summarize_ticket(self, subject: str, description: str, category: str, priority: str) -> str:
        prompt = f"""Summarize this customer support ticket in 2-3 sentences.
Include: the customer's issue, context, and likely resolution.

Subject: {subject}
Category: {category}
Priority: {priority}
Description: {description[:1500]}

Summary:"""
        result = self._call(prompt, max_tokens=256)
        return result or "Summary unavailable."

    def generate_insights(self, analytics_data: Dict[str, Any]) -> str:
        data_str = json.dumps(analytics_data, indent=2, default=str)[:3000]
        prompt = f"""Analyze this customer support analytics data and provide 3-5 key business insights.
Focus on patterns, problems, and areas needing attention.

Analytics Data:
{data_str}

Key Insights:"""
        result = self._call(prompt, max_tokens=512)
        return result or "Insights unavailable."

    def answer_question(self, question: str, analytics_context: Dict[str, Any]) -> str:
        ctx_str = json.dumps(analytics_context, indent=2, default=str)[:3000]
        prompt = f"""Answer this question about customer support data using the provided analytics context.
Be specific and reference actual numbers from the data.

Question: {question}

Analytics Context:
{ctx_str}

Answer:"""
        result = self._call(prompt, max_tokens=512)
        return result or "Answer unavailable."

    def generate_recommendations(self, analytics_data: Dict[str, Any]) -> List[str]:
        data_str = json.dumps(analytics_data, indent=2, default=str)[:3000]
        prompt = f"""Based on this customer support data, provide 3-5 specific actionable recommendations.
Each recommendation should be one clear sentence.

Analytics Data:
{data_str}

Recommendations:
1."""
        result = self._call(prompt, max_tokens=512)
        if result:
            lines = [line.strip().lstrip("0123456789. ").strip()
                     for line in result.split("\n")
                     if line.strip() and len(line.strip()) > 10]
            return lines[:5] if lines else ["Unable to generate recommendations."]
        return ["Recommendations unavailable."]


class APIAIProvider(AIProvider):
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.API_AI_BASE_URL
        self.api_key = self.settings.API_AI_KEY
        self.model = self.settings.API_AI_MODEL

    def is_available(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)

    def _call(self, messages: List[Dict[str, str]], max_tokens: int = 1024) -> Optional[str]:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
            }
            resp = httpx.post(
                f"{self.base_url.rstrip('/')}/v1/chat/completions",
                json=payload, headers=headers, timeout=60.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            return None
        except Exception:
            return None

    def summarize_ticket(self, subject: str, description: str, category: str, priority: str) -> str:
        messages = [
            {"role": "system", "content": "You are a customer support analyst. Summarize tickets concisely."},
            {"role": "user", "content": f"Summarize this ticket in 2-3 sentences:\nSubject: {subject}\nCategory: {category}\nPriority: {priority}\nDescription: {description[:1500]}"},
        ]
        return self._call(messages, 256) or "Summary unavailable."

    def generate_insights(self, analytics_data: Dict[str, Any]) -> str:
        data_str = json.dumps(analytics_data, indent=2, default=str)[:4000]
        messages = [
            {"role": "system", "content": "You are a customer support analyst. Provide clear business insights."},
            {"role": "user", "content": f"Analyze this data and provide 3-5 key insights:\n{data_str}"},
        ]
        return self._call(messages, 768) or "Insights unavailable."

    def answer_question(self, question: str, analytics_context: Dict[str, Any]) -> str:
        ctx_str = json.dumps(analytics_context, indent=2, default=str)[:4000]
        messages = [
            {"role": "system", "content": "You are a customer support data analyst. Answer questions using provided data."},
            {"role": "user", "content": f"Question: {question}\n\nData:\n{ctx_str}"},
        ]
        return self._call(messages, 512) or "Answer unavailable."

    def generate_recommendations(self, analytics_data: Dict[str, Any]) -> List[str]:
        data_str = json.dumps(analytics_data, indent=2, default=str)[:4000]
        messages = [
            {"role": "system", "content": "You are a customer support consultant. Provide actionable recommendations."},
            {"role": "user", "content": f"Provide 3-5 specific recommendations based on this data:\n{data_str}"},
        ]
        result = self._call(messages, 512)
        if result:
            lines = [line.strip().lstrip("0123456789. ").strip()
                     for line in result.split("\n")
                     if line.strip() and len(line.strip()) > 10]
            return lines[:5] if lines else ["Unable to generate recommendations."]
        return ["Recommendations unavailable."]
