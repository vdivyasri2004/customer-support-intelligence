import re
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    subcategory: Optional[str] = None


CATEGORY_KEYWORDS = {
    "Billing": {
        "keywords": ["bill", "billing", "invoice", "charge", "payment", "price", "cost", "fee", "account balance", "statement", "transaction", "overcharge", "double charge", "wrong amount"],
        "weight": 1.0,
    },
    "Technical Issue": {
        "keywords": ["bug", "error", "crash", "glitch", "not working", "broken", "technical", "software", "hardware", "update", "version", "compatibility", "loading", "freeze", "timeout", "slow", "performance"],
        "weight": 1.0,
    },
    "Account Access": {
        "keywords": ["account", "access", "locked out", "cannot access", "permission", "role", "profile", "settings", "verify", "verification", "identity", "username", "email address"],
        "weight": 1.0,
    },
    "Product Issue": {
        "keywords": ["product", "defective", "damaged", "quality", "missing parts", "wrong item", "wrong size", "material", "design", "manufacturing", "defect", "warranty"],
        "weight": 0.9,
    },
    "Shipping": {
        "keywords": ["shipping", "delivery", "tracking", "package", "order", "shipment", "courier", "transit", "delivered", "address", "lost package", "late delivery", "delayed"],
        "weight": 1.0,
    },
    "Refund": {
        "keywords": ["refund", "money back", "return", "exchange", "reimburse", "credit", "reversal", "dispute", "chargeback"],
        "weight": 1.0,
    },
    "Subscription": {
        "keywords": ["subscription", "subscribe", "unsubscribe", "plan", "renewal", "renew", "cancel", "tier", "upgrade", "downgrade", "trial", "monthly", "annual", "membership"],
        "weight": 1.0,
    },
    "Login": {
        "keywords": ["login", "log in", "sign in", "password", "forgot password", "reset password", "two-factor", "2fa", "mfa", "authentication", "otp", "verify email"],
        "weight": 1.0,
    },
    "Payment": {
        "keywords": ["payment", "pay", "checkout", "credit card", "debit", "paypal", "wire", "bank", "transaction failed", "declined", "insufficient funds", "payment method", "card expired"],
        "weight": 1.0,
    },
    "Feature Request": {
        "keywords": ["feature", "request", "suggestion", "improve", "add", "would like", "wish", "enhancement", "new feature", "capability", "option", "customize", "integration"],
        "weight": 0.9,
    },
}

SUBCATEGORY_HINTS = {
    "Billing": ["overcharge", "double charge", "wrong amount", "invoice", "statement"],
    "Technical Issue": ["bug", "crash", "performance", "compatibility", "loading"],
    "Account Access": ["locked out", "permission", "profile", "verification"],
    "Shipping": ["late delivery", "lost package", "wrong address", "tracking"],
    "Refund": ["full refund", "partial refund", "exchange", "return"],
    "Subscription": ["cancel", "renewal", "upgrade", "downgrade", "trial"],
    "Login": ["forgot password", "two-factor", "locked account", "otp"],
    "Payment": ["declined", "failed", "card expired", "insufficient funds"],
    "Product Issue": ["defective", "damaged", "missing", "wrong item"],
    "Feature Request": ["new feature", "improvement", "integration", "customization"],
}


def classify_ticket(subject: Optional[str], description: Optional[str]) -> ClassificationResult:
    combined = ""
    if subject:
        combined += subject + " "
    if description:
        combined += description

    combined_lower = combined.lower()
    if not combined_lower.strip():
        return ClassificationResult(category="Other", confidence=0.0)

    scores = {}
    for category, config in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in config["keywords"]:
            if keyword in combined_lower:
                score += 1
        scores[category] = score * config["weight"]

    if not scores or max(scores.values()) == 0:
        return ClassificationResult(category="Other", confidence=0.2)

    best_category = max(scores, key=scores.get)
    max_score = scores[best_category]
    total_score = sum(scores.values())
    confidence = min(max_score / max(total_score, 1), 0.95)
    confidence = max(confidence, 0.3)

    subcategory = None
    if best_category in SUBCATEGORY_HINTS:
        for hint in SUBCATEGORY_HINTS[best_category]:
            if hint in combined_lower:
                subcategory = hint.title()
                break

    return ClassificationResult(
        category=best_category,
        confidence=round(confidence, 2),
        subcategory=subcategory,
    )


def batch_classify(subjects: List[Optional[str]], descriptions: List[Optional[str]]) -> List[ClassificationResult]:
    return [classify_ticket(s, d) for s, d in zip(subjects, descriptions)]
