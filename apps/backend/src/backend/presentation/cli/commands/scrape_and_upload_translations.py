import logging.config
import random
from itertools import chain

import click

from backend.infrastructure.xkcd import (
    XkcdDEScraper,
    XkcdESScraper,
    XkcdFRScraper,
    XkcdRUScraper,
    XkcdZHScraper,
)
from backend.presentation.cli.common import (
    async_command,
    clean_up,
    get_number_comic_id_map,
    positive_number,
    upload_one_translation,
)
from backend.presentation.cli.progress import ProgressChunkedRunner, progress_factory

logger = logging.getLogger(__name__)


@click.command()
@click.option("--chunk_size", type=int, default=100, callback=positive_number)
@click.option("--delay", type=float, default=1, callback=positive_number)
@click.pass_context
@clean_up
@async_command
async def scrape_and_upload_translations_command(
    ctx: click.Context,
    chunk_size: int,
    delay: int,
) -> None:
    container = ctx.meta["container"]

    number_comic_id_map = await get_number_comic_id_map(container)
    db_numbers = set(number_comic_id_map.keys())

    with progress_factory() as progress:
        runner = ProgressChunkedRunner(progress, chunk_size, delay)

        ru_scraper: XkcdRUScraper = await container.get(XkcdRUScraper)
        ru_translation_list = await runner.run(
            desc=f"Russian translations scraping ({ru_scraper.BASE_URL}):",
            coro=ru_scraper.fetch_one,
            data=list(db_numbers & set(await ru_scraper.get_all_nums())),
        )

        de_scraper: XkcdDEScraper = await container.get(XkcdDEScraper)
        latest = await de_scraper.fetch_latest_number()
        de_translation_list = await runner.run(
            desc=f"Deutsch translations scraping ({de_scraper.BASE_URL}):",
            coro=de_scraper.fetch_one,
            data=[n for n in db_numbers if n <= latest],
            known_total=False,
        )

        es_scraper: XkcdESScraper = await container.get(XkcdESScraper)
        es_translation_list = await runner.run(
            desc=f"Spanish translations scraping ({es_scraper.BASE_URL})",
            coro=es_scraper.fetch_one,
            data=await es_scraper.fetch_all_links(),
            known_total=False,
            filter_numbers=db_numbers,
        )

        fr_scraper: XkcdFRScraper = await container.get(XkcdFRScraper)
        fr_translation_list = await runner.run(
            desc=f"French translations scraping ({fr_scraper.BASE_URL}):",
            coro=fr_scraper.fetch_one,
            data=list(db_numbers & set((await fr_scraper.fetch_number_data_map()).keys())),
        )

        zh_scraper: XkcdZHScraper = await container.get(XkcdZHScraper)
        zh_translation_list = await runner.run(
            desc=f"Chinese translations scraping ({zh_scraper.BASE_URL}):",
            coro=zh_scraper.fetch_one,
            data=[
                link
                for link in await zh_scraper.fetch_all_links()
                if int(link.query["id"]) in db_numbers
            ],
        )

        scraped_translations = list(
            chain(
                ru_translation_list,
                de_translation_list,
                es_translation_list,
                fr_translation_list,
                zh_translation_list,
            )
        )

        random.shuffle(scraped_translations)  # reduce DDOS when downloading images
        await runner.run(
            desc="Translations uploading:",
            coro=upload_one_translation,
            data=scraped_translations,
            number_comic_id_map=number_comic_id_map,
            container=container,
        )
