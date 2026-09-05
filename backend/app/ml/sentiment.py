import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SentimentResult:
    sentiment: str  # Positive, Neutral, Negative
    score: float  # -1.0 to 1.0


POSITIVE_WORDS = {
    "great", "excellent", "good", "fantastic", "wonderful", "amazing", "love",
    "happy", "pleased", "satisfied", "thanks", "thank", "helpful", "perfect",
    "awesome", "outstanding", "brilliant", "superb", "terrific", "impressive",
    "delighted", "appreciate", "resolved", "fixed", "working", "fast", "quick",
    "easy", "smooth", "seamless", "pleasant", "recommend", "best", "quality",
    "reliable", "efficient", "friendly", "professional", "courteous", "prompt",
    "reasonable", "fair", "solved", "issue", "beautiful", "clean"
}

NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "horrible", "worst", "hate", "angry", "frustrated",
    "disappointed", "annoyed", "upset", "unhappy", "poor", "slow", "broken",
    "useless", "waste", "rip", "scam", "unacceptable", "ridiculous", "absurd",
    "disgusting", "infuriating", "pathetic", "dreadful", "lousy", "mediocre",
    "incompetent", "neglect", "ignore", "refuse", "denied", "denial", "rejected",
    "fail", "failure", "error", "crash", "bug", "glitch", "defect", "damage",
    "loss", "lost", "stolen", "fraud", "deception", "lie", "cheat", "misleading",
    "unfair", "overcharge", "expensive", "overpriced", "waiting", "waited",
    "never", "still", "again", "problem", "issue", "complaint", "urgent",
    "escalate", "escalation", "compensation", "refund", "cancel", "cancellation"
}

NEGATION_WORDS = {"not", "no", "never", "neither", "nor", "hardly", "barely", "doesn't", "don't", "didn't", "wasn't", "weren't", "isn't", "aren't", "won't", "wouldn't", "couldn't", "shouldn't", "can't", "cannot"}

INTENSIFIERS = {"very", "really", "extremely", "incredibly", "absolutely", "totally", "completely", "utterly", "highly", "deeply"}


def analyze_sentiment(text: str) -> SentimentResult:
    if not text:
        return SentimentResult(sentiment="Neutral", score=0.0)

    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)

    pos_count = 0
    neg_count = 0
    has_negation = False

    for i, word in enumerate(words):
        if word in NEGATION_WORDS:
            has_negation = True
            continue

        if word in POSITIVE_WORDS:
            if has_negation:
                neg_count += 1.5
            else:
                pos_count += 1
            has_negation = False
        elif word in NEGATIVE_WORDS:
            if has_negation:
                pos_count += 0.5
            else:
                neg_count += 1
            has_negation = False
        else:
            has_negation = False

    # Exclamation marks can intensify sentiment
    exclamation_count = text.count("!")
    if exclamation_count > 2:
        pos_count *= 1.2
        neg_count *= 1.2

    # ALL CAPS suggests emphasis
    caps_words = len(re.findall(r'\b[A-Z]{2,}\b', text))
    if caps_words > 0:
        neg_count *= 1.3

    total = pos_count + neg_count
    if total == 0:
        return SentimentResult(sentiment="Neutral", score=0.0)

    score = (pos_count - neg_count) / total
    score = max(-1.0, min(1.0, score))

    if score > 0.15:
        sentiment = "Positive"
    elif score < -0.15:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return SentimentResult(sentiment=sentiment, score=round(score, 3))


def batch_analyze_sentiment(texts: List[str]) -> List[SentimentResult]:
    return [analyze_sentiment(text) for text in texts]


def analyze_ticket_sentiment(subject: Optional[str], description: Optional[str]) -> SentimentResult:
    combined = ""
    if subject:
        combined += subject + " "
    if description:
        combined += description
    return analyze_sentiment(combined.strip())
