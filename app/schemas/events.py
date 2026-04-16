from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentCreatedEvent(BaseModel):
    payment_id: UUID
    webhook_url: str


class DeadLetterEvent(BaseModel):
    event_type: str
    reason: str
    original_payload: dict[str, Any] = Field(default_factory=dict)
    failed_at: datetime
