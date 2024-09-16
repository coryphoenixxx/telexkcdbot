import importlib.resources
from collections.abc import AsyncIterable

from dishka import Provider, Scope, alias, provide
from faststream.nats import JStream, NatsBroker
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
)

from backend.application.comic.interfaces import (
    ComicRepoInterface,
    ImageConverterInterface,
    TagRepoInterface,
    TempFileManagerInterface,
    TranslationImageFileManagerInterface,
    TranslationImageRepoInterface,
    TranslationRepoInterface,
)
from backend.application.comic.services import (
    ComicDeleteService,
    ComicReadService,
    ComicWriteService,
    TagService,
    TranslationImageService,
)
from backend.application.common.dtos import ImageFormat
from backend.application.common.interfaces import (
    PublisherRouterInterface,
    TransactionManagerInterface,
)
from backend.application.upload.upload_image_manager import UploadImageManager
from backend.infrastructure.broker.config import NatsConfig
from backend.infrastructure.broker.publisher_router import PublisherRouter
from backend.infrastructure.config_loader import load_config
from backend.infrastructure.database.config import DbConfig
from backend.infrastructure.database.main import build_postgres_url, create_db_engine
from backend.infrastructure.database.repositories import (
    ComicRepo,
    TagRepo,
    TranslationImageRepo,
    TranslationRepo,
)
from backend.infrastructure.database.transaction import TransactionManager
from backend.infrastructure.downloader import Downloader
from backend.infrastructure.filesystem import TempFileManager, TranslationImageFileManager
from backend.infrastructure.filesystem.config import FilesystemConfig
from backend.infrastructure.http_client import AsyncHttpClient
from backend.infrastructure.image_converter import ImageConverter
from backend.infrastructure.xkcd import (
    XkcdDEScraper,
    XkcdESScraper,
    XkcdExplainScraper,
    XkcdFRScraper,
    XkcdOriginalScraper,
    XkcdRUScraper,
    XkcdZHScraper,
)
from backend.presentation.api.config import APIConfig
from backend.presentation.tg_bot.config import BotConfig


class DatabaseConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_db_config(self) -> DbConfig:
        return load_config(DbConfig, scope="db")


class BrokerConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_broker_config(self) -> NatsConfig:
        return load_config(NatsConfig, scope="nats")


class APIConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_api_config(self) -> APIConfig:
        return load_config(APIConfig, scope="api")


class BotConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_bot_config(self) -> BotConfig:
        return load_config(BotConfig, scope="bot")


class FilesystemConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_fs_config(self) -> FilesystemConfig:
        return load_config(FilesystemConfig, scope="fs")


class TransactionManagerProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_db_engine(self, config: DbConfig) -> AsyncIterable[AsyncEngine]:
        engine = create_db_engine(
            build_postgres_url(config),
            echo=config.echo,
            echo_pool=config.echo,
            pool_size=config.pool_size,
            max_overflow=20,
        )
        yield engine
        await engine.dispose()

    @provide(scope=Scope.REQUEST)
    async def provide_db_session(
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
    async def provide_transaction_manager(
        self,
        session: AsyncSession,
    ) -> AsyncIterable[TransactionManager]:
        async with TransactionManager(session) as transaction:
            yield transaction

    transaction_interface = alias(source=TransactionManager, provides=TransactionManagerInterface)


class FileManagersProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_temp_file_manager(self, config: FilesystemConfig) -> TempFileManager:
        config.temp_dir.mkdir(exist_ok=True)
        return TempFileManager(
            temp_dir=config.temp_dir,
            size_limit=config.upload_max_size,
        )

    @provide(scope=Scope.APP)
    async def provide_translation_image_file_manager(
        self,
        config: FilesystemConfig,
        temp_file_manager: TempFileManager,
    ) -> TranslationImageFileManager:
        return TranslationImageFileManager(
            static_dir=config.static_dir,
            temp_file_manager=temp_file_manager,
        )

    @provide(scope=Scope.APP)
    def provide_upload_image_manager(
        self,
        temp_file_manager: TempFileManager,
    ) -> UploadImageManager:
        return UploadImageManager(temp_file_manager, tuple(ImageFormat))

    image_converter = provide(ImageConverter, scope=Scope.APP)

    image_converter_interface = alias(source=ImageConverter, provides=ImageConverterInterface)
    temp_file_manager_interface = alias(source=TempFileManager, provides=TempFileManagerInterface)
    translation_image_file_manager_interface = alias(
        source=TranslationImageFileManager, provides=TranslationImageFileManagerInterface
    )


class PublisherRouterProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_publisher_router(
        self,
        config: NatsConfig,
    ) -> AsyncIterable[PublisherRouter]:
        broker = NatsBroker(config.url)

        stream = JStream(name="stream_name", max_age=60 * 60, declare=True)

        converter_publisher = broker.publisher(subject="images.convert", stream=stream)
        new_comic_publisher = broker.publisher(subject="comics.new", stream=stream)

        broker.setup_publisher(converter_publisher)
        broker.setup_publisher(new_comic_publisher)

        await broker.start()
        yield PublisherRouter(converter_publisher, new_comic_publisher)
        await broker.close()

    publisher_router_interface = alias(source=PublisherRouter, provides=PublisherRouterInterface)


class RepositoriesProvider(Provider):
    scope = Scope.REQUEST

    comic_repo = provide(ComicRepo)
    translation_repo = provide(TranslationRepo)
    translation_image_repo = provide(TranslationImageRepo)
    tag_repo = provide(TagRepo)

    comic_repo_interface = alias(source=ComicRepo, provides=ComicRepoInterface)
    translation_repo_interface = alias(source=TranslationRepo, provides=TranslationRepoInterface)
    translation_image_repo_interface = alias(
        source=TranslationImageRepo, provides=TranslationImageRepoInterface
    )
    tag_repo_interface = alias(source=TagRepo, provides=TagRepoInterface)


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
    async def provide_async_http_client(self) -> AsyncIterable[AsyncHttpClient]:
        async with AsyncHttpClient() as client:
            yield client

    @provide(scope=Scope.APP)
    async def provide_downloader(
        self,
        http_client: AsyncHttpClient,
        temp_file_manager: TempFileManager,
    ) -> Downloader:
        return Downloader(
            http_client=http_client,
            temp_file_manager=temp_file_manager,
        )


class ScrapersProvider(Provider):
    scope = Scope.APP

    @provide(scope=Scope.APP)
    async def provide_xkcd_explain_scraper(self, client: AsyncHttpClient) -> XkcdExplainScraper:
        with importlib.resources.open_text("assets", "bad_tags.txt") as f:
            bad_tags = {line.lower() for line in f.read().splitlines() if line}

        return XkcdExplainScraper(client, bad_tags)

    xkcd_original_scraper = provide(XkcdOriginalScraper)

    xkcd_ru_scraper = provide(XkcdRUScraper)
    xkcd_de_scraper = provide(XkcdDEScraper)
    xkcd_es_scraper = provide(XkcdESScraper)
    xkcd_fr_scraper = provide(XkcdFRScraper)
    xkcd_zh_scraper = provide(XkcdZHScraper)
