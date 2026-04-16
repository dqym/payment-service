import asyncio
from datetime import datetime, timezone

from faststream.rabbit import RabbitBroker, RabbitQueue

from app.core.config import Settings
from app.domain.exceptions import PaymentNotFoundError
from app.domain.use_cases.process_payment import ProcessPaymentUseCase
from app.infrastructure.http.webhook_client import WebhookClient
from app.infrastructure.rabbit.topology import PAYMENTS_DLQ_ROUTING_KEY, PAYMENTS_EXCHANGE, PAYMENTS_NEW_QUEUE
from app.schemas.events import DeadLetterEvent, PaymentCreatedEvent
from app.schemas.payment import WebhookPaymentResult


def register_payment_consumer(
    broker: RabbitBroker,
    settings: Settings,
    process_payment_use_case: ProcessPaymentUseCase,
    webhook_client: WebhookClient,
) -> None:
    queue = RabbitQueue(
        PAYMENTS_NEW_QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": PAYMENTS_EXCHANGE,
            "x-dead-letter-routing-key": PAYMENTS_DLQ_ROUTING_KEY,
        },
    )

    @broker.subscriber(queue)
    async def handle_new_payment(event: PaymentCreatedEvent) -> None:
        processing_error: Exception | None = None

        for attempt in range(1, settings.consumer_max_attempts + 1):
            try:
                payment = await process_payment_use_case(event.payment_id)
                payload = WebhookPaymentResult.model_validate(payment)
                await webhook_client.send(event.webhook_url, payload.model_dump(mode="json"))
                return
            except PaymentNotFoundError as exc:
                processing_error = exc
                break
            except Exception as exc:
                processing_error = exc
                if attempt == settings.consumer_max_attempts:
                    break
                await asyncio.sleep(2 ** (attempt - 1))

        failed_event = DeadLetterEvent(
            event_type="payment_processing_failed",
            reason=str(processing_error or "unknown error"),
            original_payload=event.model_dump(mode="json"),
            failed_at=datetime.now(timezone.utc),
        )
        await broker.publish(
            failed_event.model_dump(mode="json"),
            exchange=PAYMENTS_EXCHANGE,
            routing_key=PAYMENTS_DLQ_ROUTING_KEY,
        )
