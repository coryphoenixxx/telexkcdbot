import asyncio

import click
import uvloop
from dishka import make_async_container

from backend.main.ioc.providers import (
    BrokerProvider,
    ComicServicesProvider,
    ConfigsProvider,
    DatabaseProvider,
    FileManagersProvider,
    HTTPProviders,
    RepositoriesProvider,
    ScrapersProvider,
    TagServiceProvider,
    TranslationImageServiceProvider,
)
from backend.presentation.cli.commands.extract_and_upload_prescraped_translations import (
    extract_and_upload_prescraped_translations_command,
)
from backend.presentation.cli.commands.scrape_and_upload_origin import (
    scrape_and_upload_origin_command,
)
from backend.presentation.cli.commands.scrape_and_upload_translations import (
    scrape_and_upload_translations_command,
)


@click.group()
@click.pass_context
def main(context: click.Context) -> None:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    container = make_async_container(
        ConfigsProvider(),
        DatabaseProvider(),
        FileManagersProvider(),
        HTTPProviders(),
        ScrapersProvider(),
        ComicServicesProvider(),
        TranslationImageServiceProvider(),
        TagServiceProvider(),
        RepositoriesProvider(),
        BrokerProvider(),
    )

    context.meta["container"] = container


main.add_command(
    scrape_and_upload_origin_command,
    name="scrape_and_upload_origin",
)
main.add_command(
    scrape_and_upload_translations_command,
    name="scrape_and_upload_translations",
)
main.add_command(
    extract_and_upload_prescraped_translations_command,
    name="extract_and_upload_prescraped_translations",
)