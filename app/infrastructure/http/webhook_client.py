import httpx


class WebhookClient:
    def __init__(self, timeout_seconds: float) -> None:
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def send(self, webhook_url: str, payload: dict) -> None:
        response = await self._client.post(webhook_url, json=payload)
        response.raise_for_status()

    async def close(self) -> None:
        await self._client.aclose()
