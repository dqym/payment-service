from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from app.api.router import router as payments_router
from app.core.config import get_settings
from app.core.dishka.container import create_async_container


def build_app() -> FastAPI:
	settings = get_settings()
	app = FastAPI(title=settings.app_name, docs_url="/api/docs", redoc_url="/api/redoc")
	app.include_router(payments_router)

	container = create_async_container()
	setup_dishka(container=container, app=app)

	return app


app = build_app()

