import os
import anthropic
from dotenv import load_dotenv

from app.models import UnifiedMessage
from app.property_context import PROPERTY_CONTEXT

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")


def build_prompt(unified_message: UnifiedMessage) -> str:
    return f"""
You are a guest communication assistant for Nistula.

Your task:
Draft a polite, clear, and helpful reply to the guest message.

Rules:
- Do not invent information outside the provided property context.
- If the question involves availability, pricing, check-in, WiFi, chef, or cancellation, use the property context.
- If the message is a complaint, acknowledge the issue empathetically and say that the team will look into it urgently.
- Keep the reply concise and guest-friendly.
- Do not mention internal confidence scores, classification, or backend logic.
- Return only the drafted reply text.

Property context:
{PROPERTY_CONTEXT}

Guest message details:
Guest name: {unified_message.guest_name}
Source: {unified_message.source}
Booking reference: {unified_message.booking_ref}
Property ID: {unified_message.property_id}
Query type: {unified_message.query_type}
Guest message: {unified_message.message_text}
"""


def generate_reply(unified_message: UnifiedMessage) -> tuple[str, bool]:
    try:
        prompt = build_prompt(unified_message)

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        drafted_reply = response.content[0].text.strip()
        return drafted_reply, True

    except Exception as error:
        fallback_reply = (
            f"Hi {unified_message.guest_name}, thank you for your message. "
            "Our team has received your request and will get back to you shortly."
        )

        print(f"Claude API error: {error}")
        return fallback_reply, False