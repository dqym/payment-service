from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.domain.use_cases.create_payment import CreatePaymentUseCase
from app.domain.use_cases.get_payment import GetPaymentUseCase
from app.infrastructure.db.session import build_async_engine, build_session_factory
from app.infrastructure.db.uow import SqlAlchemyUnitOfWorkFactory


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_settings(self) -> Settings:
        return get_settings()

    @provide(scope=Scope.APP)
    def provide_engine(self, settings: Settings) -> AsyncEngine:
        return build_async_engine(settings.database_url)

    @provide(scope=Scope.APP)
    def provide_session_factory(
        self,
        engine: AsyncEngine,
    ) -> async_sessionmaker[AsyncSession]:
        return build_session_factory(engine)

    @provide(scope=Scope.APP)
    def provide_uow_factory(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> SqlAlchemyUnitOfWorkFactory:
        return SqlAlchemyUnitOfWorkFactory(session_factory)

    @provide(scope=Scope.APP)
    def provide_create_payment_use_case(
        self,
        uow_factory: SqlAlchemyUnitOfWorkFactory,
    ) -> CreatePaymentUseCase:
        return CreatePaymentUseCase(uow_factory)

    @provide(scope=Scope.APP)
    def provide_get_payment_use_case(
        self,
        uow_factory: SqlAlchemyUnitOfWorkFactory,
    ) -> GetPaymentUseCase:
        return GetPaymentUseCase(uow_factory)
