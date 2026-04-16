import asyncio
from datetime import timedelta

from faststream.rabbit import RabbitBroker

from app.domain.entities import utc_now
from app.domain.repositories import UnitOfWorkFactory
from app.infrastructure.rabbit.topology import PAYMENTS_EXCHANGE


class OutboxDispatcher:
    def __init__(
        self,
        broker: RabbitBroker,
        uow_factory: UnitOfWorkFactory,
        poll_interval_seconds: float,
    ) -> None:
        self._broker = broker
        self._uow_factory = uow_factory
        self._poll_interval_seconds = poll_interval_seconds

    async def run_forever(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            published_count = await self.dispatch_once()
            if published_count == 0:
                await asyncio.sleep(self._poll_interval_seconds)

    async def dispatch_once(self) -> int:
        async with self._uow_factory() as uow:
            messages = await uow.outbox.get_ready_messages(limit=100)
            if not messages:
                return 0

            for message in messages:
                try:
                    await self._broker.publish(
                        message.payload,
                        exchange=PAYMENTS_EXCHANGE,
                        routing_key=message.routing_key,
                        message_id=str(message.id),
                    )
                    await uow.outbox.mark_published(message.id)
                except Exception as exc:
                    backoff_seconds = min(2 ** max(message.attempts, 1), 60)
                    await uow.outbox.mark_failed(
                        message.id,
                        error=str(exc),
                        next_attempt_at=utc_now() + timedelta(seconds=backoff_seconds),
                    )

            await uow.commit()
            return len(messages)
