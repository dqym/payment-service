from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class OutboxStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass(slots=True)
class Payment:
    id: UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None

    @classmethod
    def create_pending(
        cls,
        amount: Decimal,
        currency: Currency,
        description: str,
        metadata: dict[str, Any],
        idempotency_key: str,
        webhook_url: str,
    ) -> "Payment":
        return cls(
            id=uuid4(),
            amount=amount,
            currency=currency,
            description=description,
            metadata=metadata,
            status=PaymentStatus.PENDING,
            idempotency_key=idempotency_key,
            webhook_url=webhook_url,
            created_at=utc_now(),
            processed_at=None,
        )

    def mark_processed(self, next_status: PaymentStatus) -> None:
        self.status = next_status
        self.processed_at = utc_now()


@dataclass(slots=True)
class OutboxMessage:
    id: UUID
    event_type: str
    routing_key: str
    payload: dict[str, Any]
    status: OutboxStatus
    attempts: int
    available_at: datetime
    created_at: datetime
    published_at: datetime | None
    error: str | None

    @classmethod
    def payment_created(cls, payment: Payment) -> "OutboxMessage":
        now = utc_now()
        return cls(
            id=uuid4(),
            event_type="payment.created",
            routing_key="payments.new",
            payload={
                "payment_id": str(payment.id),
                "webhook_url": payment.webhook_url,
            },
            status=OutboxStatus.PENDING,
            attempts=0,
            available_at=now,
            created_at=now,
            published_at=None,
            error=None,
        )
