from uuid import UUID

from app.domain.entities import Payment
from app.domain.exceptions import PaymentNotFoundError
from app.domain.repositories import UnitOfWorkFactory


class GetPaymentUseCase:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def __call__(self, payment_id: UUID) -> Payment:
        async with self._uow_factory() as uow:
            payment = await uow.payments.get_by_id(payment_id)
            if payment is None:
                raise PaymentNotFoundError(str(payment_id))

            return payment
