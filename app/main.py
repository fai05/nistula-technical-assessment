from fastapi import FastAPI, HTTPException
from uuid import uuid4

from app.models import InboundMessage, UnifiedMessage, WebhookResponse
from app.classifier import classify_query
from app.claude_client import generate_reply
from app.confidence import calculate_confidence, decide_action

app = FastAPI(
    title="Nistula Guest Message Handler",
    description="Backend system for normalising guest messages and drafting AI replies.",
    version="1.0.0"
)


@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "Nistula Guest Message Handler"
    }


@app.post("/webhook/message", response_model=WebhookResponse)
def handle_guest_message(payload: InboundMessage):
    try:
        query_type = classify_query(payload.message)

        unified_message = UnifiedMessage(
            message_id=str(uuid4()),
            source=payload.source,
            guest_name=payload.guest_name,
            message_text=payload.message,
            timestamp=payload.timestamp,
            booking_ref=payload.booking_ref,
            property_id=payload.property_id,
            query_type=query_type
        )

        drafted_reply, claude_success = generate_reply(unified_message)

        confidence_score = calculate_confidence(
            unified_message=unified_message,
            claude_success=claude_success
        )

        action = decide_action(
            query_type=query_type,
            confidence_score=confidence_score
        )

        return WebhookResponse(
            message_id=unified_message.message_id,
            query_type=unified_message.query_type,
            drafted_reply=drafted_reply,
            confidence_score=confidence_score,
            action=action
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process guest message: {str(error)}"
        )