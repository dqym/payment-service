from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Currency, OutboxMessage, OutboxStatus, Payment, PaymentStatus, utc_now
from app.infrastructure.db.models import OutboxModel, PaymentModel


class SqlAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, payment: Payment) -> None:
        model = PaymentModel(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency.value,
            description=payment.description,
            metadata_json=payment.metadata,
            status=payment.status.value,
            idempotency_key=payment.idempotency_key,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )
        self._session.add(model)

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        model = await self._session.get(PaymentModel, payment_id)
        if model is None:
            return None
        return self._to_entity(model)

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        statement = select(PaymentModel).where(PaymentModel.idempotency_key == idempotency_key)
        model = await self._session.scalar(statement)
        if model is None:
            return None
        return self._to_entity(model)

    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        processed_at: datetime | None,
    ) -> None:
        model = await self._session.get(PaymentModel, payment_id)
        if model is None:
            return

        model.status = status.value
        model.processed_at = processed_at

    @staticmethod
    def _to_entity(model: PaymentModel) -> Payment:
        return Payment(
            id=model.id,
            amount=model.amount,
            currency=Currency(model.currency),
            description=model.description,
            metadata=model.metadata_json,
            status=PaymentStatus(model.status),
            idempotency_key=model.idempotency_key,
            webhook_url=model.webhook_url,
            created_at=model.created_at,
            processed_at=model.processed_at,
        )


class SqlAlchemyOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, message: OutboxMessage) -> None:
        model = OutboxModel(
            id=message.id,
            event_type=message.event_type,
            routing_key=message.routing_key,
            payload=message.payload,
            status=message.status.value,
            attempts=message.attempts,
            available_at=message.available_at,
            created_at=message.created_at,
            published_at=message.published_at,
            error=message.error,
        )
        self._session.add(model)

    async def get_ready_messages(self, limit: int) -> list[OutboxMessage]:
        statement = (
            select(OutboxModel)
            .where(OutboxModel.status.in_([OutboxStatus.PENDING.value, OutboxStatus.FAILED.value]))
            .where(OutboxModel.available_at <= utc_now())
            .order_by(OutboxModel.created_at)
            .limit(limit)
        )
        rows = (await self._session.scalars(statement)).all()
        return [self._to_entity(row) for row in rows]

    async def mark_published(self, message_id: UUID) -> None:
        model = await self._session.get(OutboxModel, message_id)
        if model is None:
            return

        model.status = OutboxStatus.PUBLISHED.value
        model.published_at = utc_now()
        model.error = None

    async def mark_failed(self, message_id: UUID, error: str, next_attempt_at: datetime) -> None:
        model = await self._session.get(OutboxModel, message_id)
        if model is None:
            return

        model.status = OutboxStatus.FAILED.value
        model.attempts = model.attempts + 1
        model.available_at = next_attempt_at
        model.error = error

    @staticmethod
    def _to_entity(model: OutboxModel) -> OutboxMessage:
        return OutboxMessage(
            id=model.id,
            event_type=model.event_type,
            routing_key=model.routing_key,
            payload=model.payload,
            status=OutboxStatus(model.status),
            attempts=model.attempts,
            available_at=model.available_at,
            created_at=model.created_at,
            published_at=model.published_at,
            error=model.error,
        )
