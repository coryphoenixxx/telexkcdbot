from collections.abc import AsyncIterable

from dishka import Provider, Scope, provide
from faststream.nats import NatsBroker
from shared.config_loader import load_config
from shared.http_client import AsyncHttpClient
from shared.my_types import ImageFormat
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
from api.application.services.converter import Converter
from api.application.services.tag import TagService
from api.core.configs.bot import BotConfig
from api.core.configs.web import APIConfig
from api.infrastructure.database.config import DbConfig
from api.infrastructure.database.main import (
    check_db_connection,
    create_db_engine,
    create_db_session_factory,
)
from api.infrastructure.database.repositories import (
    ComicRepo,
    TranslationImageRepo,
    TranslationRepo,
)
from api.infrastructure.database.repositories.tag import TagRepo
from api.infrastructure.database.transaction import TransactionManager
from api.infrastructure.filesystem.image_file_manager import ImageFileManager
from api.presentation.broker.image_processor import ImageProcessor
from api.presentation.web.upload_image_manager import Downloader, ImageValidator, UploadImageManager


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

    @provide(scope=Scope.APP)
    async def image_file_manager(self, config: APIConfig) -> ImageFileManager:
        return ImageFileManager(
            temp_dir=config.tmp_dir,
            static_dir=config.static_dir,
            size_limit=config.upload_max_size,
            chunk_size=1024 * 64,
        )

    @provide(scope=Scope.APP)
    async def downloader(
        self,
        http_client: AsyncHttpClient,
        file_manager: ImageFileManager,
    ) -> Downloader:
        return Downloader(
            http_client=http_client,
            file_manager=file_manager,
            timeout=30.0,
            attempts=3,
            interval=1,
        )

    @provide(scope=Scope.APP)
    def image_validator(self) -> ImageValidator:
        return ImageValidator(supported_formats=tuple(ImageFormat))

    @provide(scope=Scope.APP)
    def upload_image_manager(
        self,
        file_manager: ImageFileManager,
        downloader: Downloader,
        validator: ImageValidator,
    ) -> UploadImageManager:
        return UploadImageManager(file_manager, downloader, validator)

    @provide(scope=Scope.APP)
    def image_processor(self) -> ImageProcessor:
        return ImageProcessor()

    @provide(scope=Scope.APP)
    def converter(self, broker: NatsBroker) -> Converter:
        return Converter(broker)


class BrokerProvider(Provider):
    @provide(scope=Scope.APP)
    async def broker(self) -> AsyncIterable[NatsBroker]:
        broker = NatsBroker()
        await broker.start()
        yield broker
        await broker.close()


class RepositoriesProvider(Provider):
    scope = Scope.REQUEST

    comic_repo = provide(ComicRepo)
    translation_repo = provide(TranslationRepo)
    translation_image_repo = provide(TranslationImageRepo)
    tag_repo = provide(TagRepo)


class ServicesProvider(Provider):
    scope = Scope.REQUEST

    comic_service = provide(ComicService)
    translation_service = provide(TranslationService)
    translation_image_service = provide(TranslationImageService)
    tag_service = provide(TagService)
