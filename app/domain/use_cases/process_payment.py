import asyncio
import random
from uuid import UUID

from app.domain.entities import Payment, PaymentStatus
from app.domain.exceptions import PaymentNotFoundError
from app.domain.repositories import UnitOfWorkFactory


class ProcessPaymentUseCase:
    def __init__(self, uow_factory: UnitOfWorkFactory, success_probability: float = 0.9) -> None:
        self._uow_factory = uow_factory
        self._success_probability = success_probability

    async def __call__(self, payment_id: UUID) -> Payment:
        async with self._uow_factory() as uow:
            payment = await uow.payments.get_by_id(payment_id)
            if payment is None:
                raise PaymentNotFoundError(str(payment_id))

            if payment.status != PaymentStatus.PENDING:
                return payment

            await asyncio.sleep(random.uniform(2.0, 5.0))

            next_status = (
                PaymentStatus.SUCCEEDED
                if random.random() <= self._success_probability
                else PaymentStatus.FAILED
            )
            payment.mark_processed(next_status)

            await uow.payments.update_status(payment.id, payment.status, payment.processed_at)
            await uow.commit()

            return payment
