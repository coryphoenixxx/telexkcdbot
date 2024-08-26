from collections.abc import AsyncIterable

from dishka import Provider, Scope, provide
from faststream.nats import NatsBroker
from faststream.nats.publisher.asyncapi import AsyncAPIPublisher
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
)

from backend.application.services import (
    ComicWriteService,
    TranslationImageService,
)
from backend.application.services.comic import ComicDeleteService, ComicReadService
from backend.application.services.tag import TagService
from backend.infrastructure.config_loader import load_config
from backend.infrastructure.database.config import DbConfig
from backend.infrastructure.database.main import (
    create_db_engine,
)
from backend.infrastructure.database.repositories import (
    ComicRepo,
    TagRepo,
    TranslationImageRepo,
    TranslationRepo,
)
from backend.infrastructure.database.transaction import TransactionManager
from backend.infrastructure.downloader import Downloader
from backend.infrastructure.filesystem import TempFileManager, TranslationImageFileManager
from backend.infrastructure.filesystem.dtos import ImageFormat
from backend.infrastructure.http_client import AsyncHttpClient
from backend.infrastructure.image_converter import ImageConverter
from backend.infrastructure.xkcd.scrapers import (
    XkcdDEScraper,
    XkcdESScraper,
    XkcdExplainScraper,
    XkcdFRScraper,
    XkcdOriginScraper,
    XkcdRUScraper,
    XkcdZHScraper,
)
from backend.main.configs.api import APIConfig
from backend.main.configs.bot import BotConfig
from backend.presentation.api.upload_image_manager import UploadImageManager


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


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def db_engine(self, config: DbConfig) -> AsyncIterable[AsyncEngine]:
        engine = create_db_engine(config)
        yield engine
        await engine.dispose()

    @provide(scope=Scope.REQUEST)
    async def db_session(
        self,
        engine: AsyncEngine,
    ) -> AsyncIterable[AsyncSession]:
        async with AsyncSession(
            bind=engine,
            expire_on_commit=False,
            autoflush=False,
        ) as session:
            yield session

    @provide(scope=Scope.REQUEST)
    async def uow(self, session: AsyncSession) -> AsyncIterable[TransactionManager]:
        async with TransactionManager(session) as uow:
            yield uow


class FileManagersProvider(Provider):
    @provide(scope=Scope.APP)
    async def temp_file_manager(self, config: APIConfig) -> TempFileManager:
        return TempFileManager(
            temp_dir=config.tmp_dir,
            size_limit=config.upload_max_size,
            chunk_size=1024 * 64,
        )

    @provide(scope=Scope.APP)
    async def image_file_manager(
        self,
        config: APIConfig,
        temp_file_manager: TempFileManager,
    ) -> TranslationImageFileManager:
        return TranslationImageFileManager(
            static_dir=config.static_dir,
            temp_file_manager=temp_file_manager,
        )

    @provide(scope=Scope.APP)
    def upload_image_manager(
        self,
        temp_file_manager: TempFileManager,
    ) -> UploadImageManager:
        return UploadImageManager(temp_file_manager, tuple(ImageFormat))

    image_converter = provide(ImageConverter, scope=Scope.APP)


class BrokerProvider(Provider):
    @provide(scope=Scope.APP)
    async def broker(self) -> AsyncIterable[NatsBroker]:
        broker = NatsBroker()
        await broker.start()
        yield broker
        await broker.close()

    @provide(scope=Scope.APP)
    async def converter_publisher(self, broker: NatsBroker) -> AsyncAPIPublisher:
        return broker.publisher(
            subject="internal.api.images.process.in",
            stream="process_images_in_stream",
        )


class RepositoriesProvider(Provider):
    scope = Scope.REQUEST

    comic_repo = provide(ComicRepo)
    translation_repo = provide(TranslationRepo)
    translation_image_repo = provide(TranslationImageRepo)
    tag_repo = provide(TagRepo)


class ComicServicesProvider(Provider):
    scope = Scope.REQUEST

    comic_create_service = provide(ComicWriteService)
    comic_delete_service = provide(ComicDeleteService)
    comic_read_service = provide(ComicReadService)


class TranslationImageServiceProvider(Provider):
    translation_image_service = provide(TranslationImageService, scope=Scope.REQUEST)


class TagServiceProvider(Provider):
    tag_service = provide(TagService, scope=Scope.REQUEST)


class HTTPProviders(Provider):
    @provide(scope=Scope.APP)
    async def async_http_client(self) -> AsyncIterable[AsyncHttpClient]:
        async with AsyncHttpClient() as client:
            yield client

    @provide(scope=Scope.APP)
    async def downloader(
        self,
        http_client: AsyncHttpClient,
        temp_file_manager: TempFileManager,
    ) -> Downloader:
        return Downloader(
            http_client=http_client,
            temp_file_manager=temp_file_manager,
            timeout=30.0,
            attempts=3,
            interval=1,
        )


class ScrapersProvider(Provider):
    scope = Scope.APP

    xkcd_origin_scraper = provide(XkcdOriginScraper)
    xkcd_explain_scraper = provide(XkcdExplainScraper)

    xkcd_ru_scraper = provide(XkcdRUScraper)
    xkcd_de_scraper = provide(XkcdDEScraper)
    xkcd_es_scraper = provide(XkcdESScraper)
    xkcd_fr_scraper = provide(XkcdFRScraper)
    xkcd_zh_scraper = provide(XkcdZHScraper)
