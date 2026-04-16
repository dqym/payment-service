from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.domain.entities import Currency, OutboxMessage, Payment
from app.domain.repositories import UnitOfWorkFactory


@dataclass(slots=True)
class CreatePaymentCommand:
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    webhook_url: str
    idempotency_key: str


class CreatePaymentUseCase:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def __call__(self, command: CreatePaymentCommand) -> Payment:
        async with self._uow_factory() as uow:
            existing_payment = await uow.payments.get_by_idempotency_key(command.idempotency_key)
            if existing_payment is not None:
                return existing_payment

            payment = Payment.create_pending(
                amount=command.amount,
                currency=command.currency,
                description=command.description,
                metadata=command.metadata,
                idempotency_key=command.idempotency_key,
                webhook_url=command.webhook_url,
            )
            outbox_message = OutboxMessage.payment_created(payment)

            await uow.payments.add(payment)
            await uow.outbox.add(outbox_message)
            try:
                await uow.commit()
            except IntegrityError:
                await uow.rollback()
                existing_payment = await uow.payments.get_by_idempotency_key(command.idempotency_key)
                if existing_payment is not None:
                    return existing_payment
                raise

            return payment
