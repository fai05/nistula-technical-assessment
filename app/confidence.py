from app.models import UnifiedMessage, QueryType, ActionType


QUERY_TYPE_BASE_SCORES = {
    QueryType.pre_sales_availability: 0.74,
    QueryType.pre_sales_pricing: 0.72,
    QueryType.post_sales_checkin: 0.76,
    QueryType.special_request: 0.63,
    QueryType.general_enquiry: 0.58,
    QueryType.complaint: 0.45,
}

INTENT_KEYWORDS = {
    QueryType.pre_sales_availability: [
        "available", "availability", "vacant", "free", "dates",
        "april", "may", "june", "book from", "stay from",
    ],
    QueryType.pre_sales_pricing: [
        "rate", "price", "cost", "charges", "tariff", "how much",
        "per night", "discount", "total",
    ],
    QueryType.post_sales_checkin: [
        "check in", "check-in", "checkout", "check-out", "wifi",
        "password", "arrival", "what time",
    ],
    QueryType.special_request: [
        "early check", "late checkout", "airport transfer", "chef",
        "decor", "birthday", "anniversary", "special request",
        "pickup", "drop",
    ],
    QueryType.complaint: [
        "not working", "not happy", "bad", "dirty", "issue", "problem",
        "complaint", "broken", "refund", "angry", "unhappy", "terrible",
        "leave early", "cancel because",
    ],
}

UNCERTAINTY_TERMS = [
    "maybe", "not sure", "i think", "possibly", "whatever",
    "anything", "somehow", "if possible", "can you confirm",
]

HIGH_RISK_TERMS = [
    "refund", "cancel because", "broken", "dirty", "not working",
    "terrible", "angry", "unhappy", "unsafe", "emergency", "legal",
]


def _count_keyword_hits(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _matched_intent_groups(text: str) -> int:
    return sum(
        1
        for keywords in INTENT_KEYWORDS.values()
        if _count_keyword_hits(text, keywords) > 0
    )


def calculate_confidence(unified_message: UnifiedMessage, claude_success: bool) -> float:
    """
    Heuristic confidence scoring.

    The score is based on:
    - Query type risk and how easy that intent is to answer from context
    - Whether Claude successfully returned a reply
    - Guest message clarity, ambiguity, and mixed intents
    - Whether useful routing fields are available
    - Whether the message contains high-risk or complaint language
    """

    text = unified_message.message_text.lower().strip()
    word_count = len(text.split())
    query_type = unified_message.query_type
    score = QUERY_TYPE_BASE_SCORES[query_type]

    if claude_success:
        score += 0.08
    else:
        score -= 0.30

    if unified_message.property_id:
        score += 0.04
    else:
        score -= 0.08

    if query_type in [
        QueryType.post_sales_checkin,
        QueryType.special_request,
        QueryType.complaint,
    ]:
        score += 0.04 if unified_message.booking_ref else -0.04
    elif unified_message.booking_ref:
        score += 0.02

    if word_count <= 3:
        score -= 0.18
    elif word_count <= 7:
        score -= 0.08

    if word_count > 45:
        score -= 0.04

    keyword_hits = _count_keyword_hits(text, INTENT_KEYWORDS.get(query_type, []))
    if keyword_hits >= 2:
        score += 0.08
    elif keyword_hits == 1:
        score += 0.05
    elif query_type != QueryType.general_enquiry:
        score -= 0.07

    matched_groups = _matched_intent_groups(text)
    if matched_groups > 1:
        score -= min(0.12, 0.04 * (matched_groups - 1))

    uncertainty_hits = _count_keyword_hits(text, UNCERTAINTY_TERMS)
    score -= min(0.12, 0.04 * uncertainty_hits)

    high_risk_hits = _count_keyword_hits(text, HIGH_RISK_TERMS)
    score -= min(0.16, 0.06 * high_risk_hits)

    if text.count("?") > 1:
        score -= min(0.08, 0.03 * (text.count("?") - 1))

    if query_type == QueryType.complaint:
        score = min(score, 0.55)
    else:
        score = min(score, 0.95)

    return round(max(0.0, min(score, 1.0)), 2)


def decide_action(query_type: QueryType, confidence_score: float) -> ActionType:
    if query_type == QueryType.complaint:
        return ActionType.escalate

    if confidence_score > 0.85:
        return ActionType.auto_send

    if confidence_score >= 0.60:
        return ActionType.agent_review

    return ActionType.escalate
