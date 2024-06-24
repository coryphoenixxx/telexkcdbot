from collections.abc import AsyncIterable

from dishka import Provider, Scope, provide
from faststream.nats import NatsBroker
from shared.config_loader import load_config
from shared.http_client import AsyncHttpClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from api.application.services import (
    ComicService,
    TranslationImageService,
    TranslationService,
)
from api.core.configs.bot import BotConfig
from api.core.configs.web import APIConfig
from api.infrastructure.database.config import DbConfig
from api.infrastructure.database.gateways import (
    ComicGateway,
    TranslationGateway,
    TranslationImageGateway,
)
from api.infrastructure.database.main import (
    check_db_connection,
    create_db_engine,
    create_db_session_factory,
)
from api.infrastructure.database.transaction import TransactionManager
from api.infrastructure.image_saver import ImageSaveHelper
from api.presentation.web.upload_reader import UploadImageHandler


class ConfigsProvider(Provider):
    @provide(scope=Scope.APP)
    def db_config(self) -> DbConfig:
        return load_config(DbConfig, scope="db")

    @provide(scope=Scope.APP)
    def api_config(self) -> APIConfig:
        return load_config(APIConfig, scope="api")

    @provide(scope=Scope.APP)
    def bot_config(self) -> BotConfig:
        return load_config(BotConfig, scope="bot")


class DbProvider(Provider):
    @provide(scope=Scope.APP)
    async def db_engine(self, config: DbConfig) -> AsyncIterable[AsyncEngine]:
        engine = create_db_engine(config)

        await check_db_connection(engine)

        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def db_session_pool(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return create_db_session_factory(engine)

    @provide(scope=Scope.REQUEST)
    async def db_session(
        self,
        session_pool: async_sessionmaker[AsyncSession],
    ) -> AsyncIterable[AsyncSession]:
        async with session_pool() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    async def uow(self, session: AsyncSession) -> AsyncIterable[TransactionManager]:
        async with TransactionManager(session) as uow:
            yield uow


class HelpersProvider(Provider):
    @provide(scope=Scope.APP)
    async def async_http_client(self) -> AsyncIterable[AsyncHttpClient]:
        async with AsyncHttpClient() as client:
            yield client

    @provide(scope=Scope.REQUEST)
    def upload_image_handler(
        self,
        config: APIConfig,
        http_client: AsyncHttpClient,
    ) -> UploadImageHandler:
        return UploadImageHandler(config, http_client)

    image_save_helper = provide(ImageSaveHelper, scope=Scope.REQUEST)


class BrokerProvider(Provider):
    @provide(scope=Scope.APP)
    async def broker(self) -> AsyncIterable[NatsBroker]:
        broker = NatsBroker()

        await broker.start()
        yield broker
        await broker.close()


class GatewaysProvider(Provider):
    scope = Scope.REQUEST

    comic_gateway = provide(ComicGateway)
    translation_gateway = provide(TranslationGateway)
    translation_image_gateway = provide(TranslationImageGateway)


class ServicesProvider(Provider):
    scope = Scope.REQUEST

    comic_service = provide(ComicService)
    translation_service = provide(TranslationService)
    translation_image_service = provide(TranslationImageService)
