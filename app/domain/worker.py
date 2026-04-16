import asyncio
from contextlib import suppress

from app.core.config import get_settings
from app.domain.use_cases.process_payment import ProcessPaymentUseCase
from app.infrastructure.db.session import build_async_engine, build_session_factory
from app.infrastructure.db.uow import SqlAlchemyUnitOfWorkFactory
from app.infrastructure.http.webhook_client import WebhookClient
from app.infrastructure.rabbit.broker import create_broker
from app.infrastructure.rabbit.consumer import register_payment_consumer
from app.infrastructure.rabbit.outbox_dispatcher import OutboxDispatcher
from app.infrastructure.rabbit.setup import declare_rabbit_topology


async def run_worker() -> None:
    settings = get_settings()

    engine = build_async_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    uow_factory = SqlAlchemyUnitOfWorkFactory(session_factory)

    broker = create_broker(settings)
    webhook_client = WebhookClient(timeout_seconds=settings.webhook_timeout_seconds)
    process_payment_use_case = ProcessPaymentUseCase(uow_factory)

    register_payment_consumer(
        broker=broker,
        settings=settings,
        process_payment_use_case=process_payment_use_case,
        webhook_client=webhook_client,
    )

    outbox_dispatcher = OutboxDispatcher(
        broker=broker,
        uow_factory=uow_factory,
        poll_interval_seconds=settings.outbox_poll_interval_seconds,
    )

    stop_event = asyncio.Event()

    await declare_rabbit_topology(settings)
    await broker.start()
    dispatcher_task = asyncio.create_task(outbox_dispatcher.run_forever(stop_event))
    try:
        await asyncio.Event().wait()
    finally:
        stop_event.set()
        dispatcher_task.cancel()
        with suppress(asyncio.CancelledError):
            await dispatcher_task
        await webhook_client.close()
        await broker.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_worker())
