import asyncio

from app.domain.worker import run_worker


if __name__ == "__main__":
    asyncio.run(run_worker())
