from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities import OutboxMessage, Payment, PaymentStatus


class PaymentRepository(Protocol):
    async def add(self, payment: Payment) -> None:
        ...

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        ...

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        ...

    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        processed_at: datetime | None,
    ) -> None:
        ...


class OutboxRepository(Protocol):
    async def add(self, message: OutboxMessage) -> None:
        ...

    async def get_ready_messages(self, limit: int) -> list[OutboxMessage]:
        ...

    async def mark_published(self, message_id: UUID) -> None:
        ...

    async def mark_failed(self, message_id: UUID, error: str, next_attempt_at: datetime) -> None:
        ...


class UnitOfWork(Protocol):
    payments: PaymentRepository
    outbox: OutboxRepository

    async def __aenter__(self) -> "UnitOfWork":
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> UnitOfWork:
        ...
