from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.ai.provider import AIProvider, UnavailableAIProvider
from app.ai.providers import LocalAIProvider, APIAIProvider
from app.models.ticket import Ticket
from app.models.dataset import Dataset
from app.analytics.engine import AnalyticsService


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    provider_type = settings.AI_PROVIDER.lower()

    if provider_type == "api" and settings.API_AI_BASE_URL and settings.API_AI_KEY:
        provider = APIAIProvider()
        if provider.is_available():
            return provider

    if provider_type == "local":
        provider = LocalAIProvider()
        if provider.is_available():
            return provider

    return UnavailableAIProvider()


class AIService:
    def __init__(self, db: Session):
        self.db = db
        self.provider = get_ai_provider()
        self.analytics_service = AnalyticsService(db)

    def is_available(self) -> bool:
        return self.provider.is_available()

    def summarize_ticket(self, ticket_id: int) -> Dict[str, Any]:
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return {"available": False, "message": "Ticket not found", "summary": ""}

        if ticket.ai_summary:
            return {"available": True, "summary": ticket.ai_summary}

        if not self.is_available():
            return {
                "available": False,
                "message": "AI provider is not available. Configure Ollama or an API provider.",
                "summary": self._generate_basic_summary(ticket),
            }

        summary = self.provider.summarize_ticket(
            subject=ticket.subject or "",
            description=ticket.description or "",
            category=ticket.category or "Unknown",
            priority=ticket.priority or "Unknown",
        )

        ticket.ai_summary = summary
        self.db.commit()

        return {"available": True, "summary": summary}

    def generate_insights(self, dataset_id: int) -> Dict[str, Any]:
        analytics = self.analytics_service.get_full_analytics(dataset_id)
        analytics_dict = analytics.model_dump()

        if not self.is_available():
            return {
                "available": False,
                "message": "AI provider is not available. Configure Ollama or an API provider.",
                "insights": self._generate_rule_based_insights(analytics_dict),
                "summary": "Showing rule-based insights (AI unavailable).",
            }

        insights_text = self.provider.generate_insights(analytics_dict)
        recommendations = self.provider.generate_recommendations(analytics_dict)

        return {
            "available": True,
            "insights_text": insights_text,
            "recommendations": recommendations,
            "analytics_summary": {
                "total_tickets": analytics.kpis.total_tickets,
                "avg_satisfaction": analytics.kpis.avg_satisfaction,
                "sla_compliance": analytics.kpis.sla_compliance,
                "negative_sentiment_pct": analytics.kpis.negative_sentiment_pct,
            },
        }

    def detect_common_issues(self, dataset_id: int) -> Dict[str, Any]:
        from app.ml.common_issues import detect_common_issues
        issues = detect_common_issues(self.db, dataset_id)
        return {
            "available": True,
            "issues": [
                {
                    "title": issue.title,
                    "frequency": issue.frequency,
                    "affected_category": issue.affected_category,
                    "avg_satisfaction": issue.avg_satisfaction,
                    "sentiment": issue.sentiment,
                    "example_tickets": issue.example_tickets,
                }
                for issue in issues
            ],
        }

    def answer_question(self, dataset_id: int, question: str) -> Dict[str, Any]:
        analytics = self.analytics_service.get_full_analytics(dataset_id)
        analytics_dict = analytics.model_dump()

        facts = {
            "total_tickets": analytics.kpis.total_tickets,
            "avg_satisfaction": analytics.kpis.avg_satisfaction,
            "sla_compliance": analytics.kpis.sla_compliance,
            "avg_response_time": analytics.kpis.avg_response_time,
            "avg_resolution_time": analytics.kpis.avg_resolution_time,
            "negative_sentiment_pct": analytics.kpis.negative_sentiment_pct,
            "high_priority_pct": analytics.kpis.high_priority_pct,
            "categories": [{"category": c.category, "count": c.count} for c in analytics.tickets_by_category],
            "agents": [{"agent": a.agent, "total": a.total, "avg_satisfaction": a.avg_satisfaction, "avg_resolution_time": a.avg_resolution_time} for a in analytics.agent_performance],
            "satisfaction_by_category": [{"category": s.category, "avg_satisfaction": s.avg_satisfaction} for s in analytics.satisfaction_by_category],
        }

        if not self.is_available():
            return {
                "available": False,
                "message": "AI provider is not available. Showing calculated facts only.",
                "question": question,
                "calculated_facts": facts,
                "answer": self._generate_facts_answer(question, facts),
            }

        answer = self.provider.answer_question(question, {"facts": facts, "analytics": analytics_dict})
        return {
            "available": True,
            "question": question,
            "answer": answer,
            "calculated_facts": facts,
        }

    def _generate_basic_summary(self, ticket: Ticket) -> str:
        parts = []
        if ticket.category:
            parts.append(f"Category: {ticket.category}")
        if ticket.priority:
            parts.append(f"Priority: {ticket.priority}")
        if ticket.subject:
            parts.append(f"Issue: {ticket.subject}")
        if ticket.status:
            parts.append(f"Status: {ticket.status}")
        return " | ".join(parts) if parts else "No summary available."

    def _generate_rule_based_insights(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        insights = []
        kpis = data.get("kpis", {})

        if kpis.get("negative_sentiment_pct", 0) > 30:
            insights.append({
                "title": "High Negative Sentiment",
                "description": f"{kpis['negative_sentiment_pct']}% of tickets have negative sentiment, indicating significant customer dissatisfaction.",
                "category": "problem",
                "severity": "warning",
            })

        if kpis.get("sla_compliance", 100) < 80:
            insights.append({
                "title": "SLA Compliance Below Target",
                "description": f"SLA compliance is at {kpis['sla_compliance']}%, below the typical 80% target.",
                "category": "problem",
                "severity": "critical",
            })

        if kpis.get("avg_satisfaction", 5) < 3.0:
            insights.append({
                "title": "Low Customer Satisfaction",
                "description": f"Average satisfaction is {kpis['avg_satisfaction']}/5, indicating poor support experience.",
                "category": "problem",
                "severity": "warning",
            })

        categories = data.get("tickets_by_category", [])
        if categories:
            top = categories[0]
            insights.append({
                "title": f"Top Category: {top['category']}",
                "description": f"{top['category']} accounts for {top['count']} tickets, the highest volume category.",
                "category": "observation",
                "severity": "info",
            })

        agents = data.get("agent_performance", [])
        if len(agents) > 1:
            sorted_agents = sorted(agents, key=lambda x: x.get("avg_satisfaction") or 0)
            lowest = sorted_agents[0]
            if lowest.get("avg_satisfaction") and lowest["avg_satisfaction"] < 3.0:
                insights.append({
                    "title": f"Agent Performance Concern: {lowest['agent']}",
                    "description": f"{lowest['agent']} has the lowest satisfaction at {lowest['avg_satisfaction']}/5.",
                    "category": "observation",
                    "severity": "info",
                })

        insights.append({
            "title": "Configure AI for Deeper Analysis",
            "description": "For more detailed insights, configure an AI provider (Ollama or API) in environment variables.",
            "category": "recommendation",
            "severity": "info",
        })

        return insights

    def _generate_facts_answer(self, question: str, facts: Dict[str, Any]) -> str:
        q = question.lower()
        parts = []

        if "common" in q and "complaint" in q or "issue" in q:
            cats = facts.get("categories", [])
            if cats:
                top3 = cats[:3]
                parts.append("Most common categories:")
                for c in top3:
                    parts.append(f"  - {c['category']}: {c['count']} tickets")

        if "satisfaction" in q:
            parts.append(f"Overall satisfaction: {facts.get('avg_satisfaction', 'N/A')}/5")
            sat_by_cat = facts.get("satisfaction_by_category", [])
            lowest = min(sat_by_cat, key=lambda x: x.get("avg_satisfaction") or 999) if sat_by_cat else None
            if lowest and lowest.get("avg_satisfaction"):
                parts.append(f"Lowest satisfaction category: {lowest['category']} ({lowest['avg_satisfaction']}/5)")

        if "agent" in q:
            agents = facts.get("agents", [])
            for a in agents[:5]:
                parts.append(f"  - {a['agent']}: {a['total']} tickets, satisfaction: {a.get('avg_satisfaction', 'N/A')}")

        if "response time" in q or "resolution time" in q:
            parts.append(f"Avg response time: {facts.get('avg_response_time', 'N/A')} min")
            parts.append(f"Avg resolution time: {facts.get('avg_resolution_time', 'N/A')} min")

        if "sla" in q:
            parts.append(f"SLA compliance: {facts.get('sla_compliance', 'N/A')}%")

        if "sentiment" in q:
            parts.append(f"Negative sentiment: {facts.get('negative_sentiment_pct', 'N/A')}%")

        if not parts:
            parts.append(f"Total tickets: {facts.get('total_tickets', 0)}")
            parts.append(f"Avg satisfaction: {facts.get('avg_satisfaction', 'N/A')}/5")
            parts.append("For AI-powered answers, configure an AI provider.")

        return "\n".join(parts)
