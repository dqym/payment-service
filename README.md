# Сервис Платежей

Асинхронный микросервис для обработки платежей, построенный на:

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 async + PostgreSQL
- RabbitMQ + FastStream
- Alembic миграциях
- паттерне Outbox
- повторных попытках consumer + DLQ
- Docker (классическая multi-container схема)

## Структура Проекта

```text
app/
  api/               # HTTP-эндпоинты
  core/              # конфиг + контейнер dishka
  domain/            # сущности + use-case + точка входа worker
  infrastructure/    # db, rabbitmq, webhooks
  schemas/           # DTO-модели
docker/              # скрипты запуска контейнеров
env/                 # env-файлы docker по сервисам
alembic/             # миграции
main.py              # FastAPI-приложение
app/domain/worker.py # Consumer + Outbox dispatcher
```

## Основные Возможности

- POST /api/v1/payments создает платеж с обязательным заголовком Idempotency-Key.
- GET /api/v1/payments/{payment_id} возвращает детали платежа.
- Аутентификация по API ключу через заголовок X-API-Key для всех эндпоинтов.
- Событие Outbox сохраняется в той же транзакции БД, что и создание платежа.
- Фоновый dispatcher публикует события из outbox в очередь payments.new.
- Consumer обрабатывает платеж асинхронно:
  - эмуляция задержки 2-5 сек;
  - 90% успешных и 10% неуспешных обработок;
  - отправка webhook-уведомления;
  - 3 повторные попытки с экспоненциальной задержкой;
  - отправка в DLQ после финального падения (payments.dlq).

## Запуск Через Docker

```bash
docker compose up -d --build
```

Переменные окружения для контейнеров вынесены в env/*.env и подключаются
в docker-compose.yaml через env_file для каждого сервиса
(api.env, worker.env, postgres.env, rabbitmq.env).

Для удобной разработки сервисы api и worker монтируют проект как bind volume
(./:/app), поэтому изменения кода сразу видны внутри контейнеров после
перезапуска сервиса.

Compose поднимает отдельные контейнеры:

- api на http://localhost:8000 (swagger на http://localhost:8000/api/docs)
- worker (consumer + outbox dispatcher)
- postgres на localhost:5432
- rabbitmq AMQP на localhost:5672
- rabbitmq management UI на http://localhost:15672

При старте контейнера api миграции применяются автоматически в
docker/start-api.sh через alembic upgrade head.

## Использование API

### Создание Платежа

```bash
curl -X POST "http://localhost:8000/api/v1/payments" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ..." \
  -H "Idempotency-Key: order-100500" \
  -d '{
    "amount": "1200.00",
    "currency": "RUB",
    "description": "Order #100500",
    "metadata": {"customer_id": "c-1"},
    "webhook_url": "https://webhook.site/your-id"
  }'
```

Пример ответа:

```json
{
  "payment_id": "0f4dc613-63f1-4d95-9c4f-a2163592ad4e",
  "status": "pending",
  "created_at": "2026-04-16T10:12:43.389290+00:00"
}
```

### Получение Платежа

```bash
curl "http://localhost:8000/api/v1/payments/0f4dc613-63f1-4d95-9c4f-a2163592ad4e" \
  -H "X-API-Key: ..."
```

## Локальный Запуск Без Docker

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Установите переменные окружения для PostgreSQL/RabbitMQ.

3. Примените миграции:

```bash
alembic upgrade head
```

4. Запустите API и worker в разных терминалах:

```bash
uvicorn main:app --reload
python -m app.domain.worker
```

## Troubleshooting

Если в Docker возникают проблемы при запуске `.sh`-файлов,
скорее всего у скриптов Windows-окончания строк (CRLF).

Преобразуйте их в Unix-формат (LF):

```bash
dos2unix docker/start-api.sh docker/start-worker.sh
```

Или сразу для всех shell-скриптов в папке `docker`:

```bash
dos2unix docker/*.sh
```
