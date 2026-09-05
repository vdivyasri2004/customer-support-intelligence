import re
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from app.models.ticket import Ticket


@dataclass
class CommonIssue:
    title: str
    frequency: int
    affected_category: str
    avg_satisfaction: Optional[float] = None
    sentiment: str = "Unknown"
    example_tickets: List[int] = field(default_factory=list)


STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her",
    "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs",
    "themselves", "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if",
    "or", "because", "as", "until", "while", "of", "at", "by", "for", "with",
    "about", "against", "between", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s",
    "t", "can", "will", "just", "don", "should", "now", "d", "ll", "m", "o", "re",
    "ve", "y", "ain", "aren", "couldn", "didn", "doesn", "hadn", "hasn", "haven",
    "isn", "ma", "mightn", "mustn", "needn", "shan", "shouldn", "wasn", "weren",
    "won", "wouldn", "also", "would", "could", "like", "get", "got", "going",
    "went", "want", "need", "know", "said", "say", "one", "two", "first", "new",
    "well", "back", "even", "still", "much", "many", "may", "might", "much",
}


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    words = [w for w in words if w not in STOP_WORDS]
    return [word for word, _ in Counter(words).most_common(top_n)]


def detect_common_issues(db: Session, dataset_id: int, limit: int = 10) -> List[CommonIssue]:
    tickets = db.query(Ticket).filter(
        Ticket.dataset_id == dataset_id,
        Ticket.subject.isnot(None),
        Ticket.description.isnot(None)
    ).all()

    if not tickets:
        return []

    # Group by similar subjects
    subject_groups: Dict[str, List[Ticket]] = defaultdict(list)
    for ticket in tickets:
        normalized = normalize_text(ticket.subject or "")
        subject_groups[normalized].append(ticket)

    # Find phrase patterns in subjects
    phrase_counter: Dict[str, List[Ticket]] = defaultdict(list)
    for ticket in tickets:
        text = (ticket.subject or "").lower()
        words = text.split()
        # Extract bigrams and trigrams
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if not all(w in STOP_WORDS for w in words[i:i+2]):
                phrase_counter[bigram].append(ticket)
        for i in range(len(words) - 2):
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            if not all(w in STOP_WORDS for w in words[i:i+3]):
                phrase_counter[trigram].append(ticket)

    # Combine short subject groups and phrases
    issue_candidates: Dict[str, List[Ticket]] = {}

    for phrase, tix in phrase_counter.items():
        if len(tix) >= 3:
            issue_candidates[phrase.title()] = tix

    for subj, tix in subject_groups.items():
        if len(tix) >= 3 and len(subj) > 5:
            title = tix[0].subject or subj
            if title not in issue_candidates:
                issue_candidates[title] = tix

    # If not enough grouped issues, fall back to keyword clustering
    if len(issue_candidates) < 3:
        keyword_tickets: Dict[str, List[Ticket]] = defaultdict(list)
        for ticket in tickets:
            text = f"{ticket.subject or ''} {ticket.description or ''}"
            keywords = extract_keywords(text, 3)
            for kw in keywords:
                keyword_tickets[kw].append(ticket)

        for kw, tix in keyword_tickets.items():
            if len(tix) >= 5:
                title = f"Tickets mentioning '{kw}'"
                if title not in issue_candidates:
                    issue_candidates[title] = tix

    # Build results
    issues = []
    for title, tix in issue_candidates.items():
        categories = [t.category for t in tix if t.category]
        most_common_cat = Counter(categories).most_common(1)
        cat = most_common_cat[0][0] if most_common_cat else "Unknown"

        sats = [t.satisfaction_score for t in tix if t.satisfaction_score is not None]
        avg_sat = round(sum(sats) / len(sats), 2) if sats else None

        sentiments = [t.sentiment for t in tix if t.sentiment]
        sent_counts = Counter(sentiments)
        dominant_sentiment = sent_counts.most_common(1)[0][0] if sent_counts else "Unknown"

        issue = CommonIssue(
            title=title,
            frequency=len(tix),
            affected_category=cat,
            avg_satisfaction=avg_sat,
            sentiment=dominant_sentiment,
            example_tickets=[t.id for t in tix[:3]],
        )
        issues.append(issue)

    issues.sort(key=lambda x: x.frequency, reverse=True)
    return issues[:limit]


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    words = text.split()
    words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    return ' '.join(words)
