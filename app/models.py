from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class SourceType(str, Enum):
    whatsapp = "whatsapp"
    booking_com = "booking_com"
    airbnb = "airbnb"
    instagram = "instagram"
    direct = "direct"


class QueryType(str, Enum):
    pre_sales_availability = "pre_sales_availability"
    pre_sales_pricing = "pre_sales_pricing"
    post_sales_checkin = "post_sales_checkin"
    special_request = "special_request"
    complaint = "complaint"
    general_enquiry = "general_enquiry"


class ActionType(str, Enum):
    auto_send = "auto_send"
    agent_review = "agent_review"
    escalate = "escalate"


class InboundMessage(BaseModel):
    source: SourceType
    guest_name: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    timestamp: str
    booking_ref: Optional[str] = None
    property_id: str


class UnifiedMessage(BaseModel):
    message_id: str
    source: SourceType
    guest_name: str
    message_text: str
    timestamp: str
    booking_ref: Optional[str] = None
    property_id: str
    query_type: QueryType


class WebhookResponse(BaseModel):
    message_id: str
    query_type: QueryType
    drafted_reply: str
    confidence_score: float
    action: ActionType