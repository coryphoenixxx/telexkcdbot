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
    ImageFileManagerInterface,
    TagRepoInterface,
    TempFileManagerInterface,
    TranslationImageRepoInterface,
    TranslationRepoInterface,
)
from backend.application.comic.services import (
    AddTranslationInteractor,
    ComicReader,
    CreateComicInteractor,
    DeleteComicInteractor,
    DeleteTagInteractor,
    DeleteTranslationDraftInteractor,
    FullUpdateComicInteractor,
    FullUpdateTranslationInteractor,
    ProcessTranslationImageInteractor,
    PublishTranslationDraftInteractor,
    TranslationReader,
    UpdateTagInteractor,
)
from backend.application.common.interfaces import (
    PublisherRouterInterface,
    TransactionManagerInterface,
)
from backend.application.config import AppConfig, FileStorageType
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
from backend.infrastructure.filesystem import ImageFSFileManager, TempFileManager
from backend.infrastructure.filesystem.config import FSConfig
from backend.infrastructure.http_client import AsyncHttpClient
from backend.infrastructure.image_converter import ImageConverter
from backend.infrastructure.s3.client import ImageS3FileManager
from backend.infrastructure.s3.config import S3Config
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
from backend.presentation.cli.config import CLIConfig
from backend.presentation.tg_bot.config import BotConfig


class AppConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_app_config(self) -> AppConfig:
        return load_config(AppConfig, scope="app")


class DatabaseConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_db_config(self) -> DbConfig:
        return load_config(DbConfig, scope="db")


class BrokerConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_broker_config(self) -> NatsConfig:
        return load_config(NatsConfig, scope="nats")


class CLIConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_cli_config(self) -> CLIConfig:
        return load_config(CLIConfig, scope="cli")


class APIConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_api_config(self) -> APIConfig:
        return load_config(APIConfig, scope="api")


class BotConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_bot_config(self) -> BotConfig:
        return load_config(BotConfig, scope="bot")


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
    async def provide_temp_file_manager(self, config: AppConfig) -> TempFileManager:
        config.temp_dir.mkdir(exist_ok=True)
        return TempFileManager(
            temp_dir=config.temp_dir,
            size_limit=config.upload_max_size,
        )

    @provide(scope=Scope.APP)
    async def provide_file_storage_interface(
        self,
        app_config: AppConfig,
    ) -> ImageFileManagerInterface:
        match app_config.file_storage:
            case FileStorageType.FS:
                config = load_config(FSConfig, scope="fs")
                return ImageFSFileManager(root_dir=config.root_dir)
            case FileStorageType.S3:
                return ImageS3FileManager(config=load_config(S3Config, scope="s3"))

    upload_image_manager = provide(UploadImageManager, scope=Scope.APP)
    image_converter = provide(ImageConverter, scope=Scope.APP)
    image_converter_interface = alias(source=ImageConverter, provides=ImageConverterInterface)

    temp_file_manager_interface = alias(source=TempFileManager, provides=TempFileManagerInterface)


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

    create_comic_interactor = provide(CreateComicInteractor)
    full_update_comic_interactor = provide(FullUpdateComicInteractor)
    delete_comic_interactor = provide(DeleteComicInteractor)
    comic_reader = provide(ComicReader)


class TagServiceProvider(Provider):
    scope = Scope.REQUEST

    update_tag_interactor = provide(UpdateTagInteractor)
    delete_tag_interactor = provide(DeleteTagInteractor)


class TranslationServicesProvider(Provider):
    scope = Scope.REQUEST

    add_translation_interactor = provide(AddTranslationInteractor)
    full_update_translation_interactor = provide(FullUpdateTranslationInteractor)
    publish_translation_draft_interactor = provide(PublishTranslationDraftInteractor)
    delete_translation_draft_interactor = provide(DeleteTranslationDraftInteractor)
    translation_reader = provide(TranslationReader)


class TranslationImageServiceProvider(Provider):
    scope = Scope.REQUEST

    translation_image_interactor = provide(ProcessTranslationImageInteractor)


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
