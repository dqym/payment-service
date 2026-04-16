import aio_pika

from app.core.config import Settings
from app.infrastructure.rabbit.topology import (
    PAYMENTS_DLQ_QUEUE,
    PAYMENTS_DLQ_ROUTING_KEY,
    PAYMENTS_EXCHANGE,
    PAYMENTS_NEW_QUEUE,
    PAYMENTS_NEW_ROUTING_KEY,
)


async def declare_rabbit_topology(settings: Settings) -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            PAYMENTS_EXCHANGE,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

        payments_new_queue = await channel.declare_queue(
            PAYMENTS_NEW_QUEUE,
            durable=True,
            arguments={
                "x-dead-letter-exchange": PAYMENTS_EXCHANGE,
                "x-dead-letter-routing-key": PAYMENTS_DLQ_ROUTING_KEY,
            },
        )
        await payments_new_queue.bind(exchange, routing_key=PAYMENTS_NEW_ROUTING_KEY)

        payments_dlq_queue = await channel.declare_queue(PAYMENTS_DLQ_QUEUE, durable=True)
        await payments_dlq_queue.bind(exchange, routing_key=PAYMENTS_DLQ_ROUTING_KEY)
