from app.models import QueryType


def classify_query(message_text: str) -> QueryType:
    """
    Rule-based query classifier.

    This is intentionally simple and explainable for the assessment.
    A production system could later replace this with an ML classifier
    or LLM-based classification.
    """

    text = message_text.lower()

    complaint_keywords = [
        "not working", "not happy", "bad", "dirty", "issue", "problem",
        "complaint", "broken", "refund", "angry", "unhappy", "terrible",
        "leave early", "cancel because"
    ]

    availability_keywords = [
        "available", "availability", "vacant", "free", "dates",
        "april", "may", "june", "book from", "stay from"
    ]

    pricing_keywords = [
        "rate", "price", "cost", "charges", "tariff", "how much",
        "per night", "discount", "total"
    ]

    checkin_keywords = [
        "check in", "check-in", "checkout", "check-out", "wifi",
        "password", "arrival", "what time"
    ]

    special_request_keywords = [
        "early check", "late checkout", "airport transfer", "chef",
        "decor", "birthday", "anniversary", "special request",
        "something special", "arrange something", "special for us",
        "pickup", "drop"
    ]

    if any(keyword in text for keyword in complaint_keywords):
        return QueryType.complaint

    if any(keyword in text for keyword in special_request_keywords):
        return QueryType.special_request

    if any(keyword in text for keyword in checkin_keywords):
        return QueryType.post_sales_checkin

    # If a message asks both availability and rate, we classify it as availability
    # because confirming dates is usually the first decision point.
    if any(keyword in text for keyword in availability_keywords):
        return QueryType.pre_sales_availability

    if any(keyword in text for keyword in pricing_keywords):
        return QueryType.pre_sales_pricing

    return QueryType.general_enquiry
