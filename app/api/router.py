from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.dependencies import verify_api_key
from app.domain.exceptions import PaymentNotFoundError
from app.domain.use_cases.create_payment import CreatePaymentCommand, CreatePaymentUseCase
from app.domain.use_cases.get_payment import GetPaymentUseCase
from app.schemas.payment import PaymentAcceptedResponse, PaymentCreateRequest, PaymentDetailsResponse

router = APIRouter(
    prefix="/api/v1/payments",
    tags=["payments"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "",
    response_model=PaymentAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@inject
async def create_payment(
    payload: PaymentCreateRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    use_case: FromDishka[CreatePaymentUseCase],
) -> PaymentAcceptedResponse:
    if not idempotency_key.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Idempotency-Key must not be empty",
        )

    payment = await use_case(
        CreatePaymentCommand(
            amount=payload.amount,
            currency=payload.currency,
            description=payload.description,
            metadata=payload.metadata,
            webhook_url=str(payload.webhook_url),
            idempotency_key=idempotency_key,
        )
    )
    return PaymentAcceptedResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    )


@router.get("/{payment_id}", response_model=PaymentDetailsResponse)
@inject
async def get_payment(
    payment_id: UUID,
    use_case: FromDishka[GetPaymentUseCase],
) -> PaymentDetailsResponse:
    try:
        payment = await use_case(payment_id)
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return PaymentDetailsResponse(
        payment_id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.metadata,
        status=payment.status,
        idempotency_key=payment.idempotency_key,
        webhook_url=payment.webhook_url,
        created_at=payment.created_at,
        processed_at=payment.processed_at,
    )
