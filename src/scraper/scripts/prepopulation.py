import asyncio
import logging

import uvloop
from alive_progress import alive_bar
from scraper.dtos import XkcdORIGINFullScrapedData, XkcdTranslationData
from scraper.scrapers import XkcdDEScraper, XkcdESScraper, XkcdOriginScraper, XkcdRUScraper
from scraper.scrapers.xkcd_cn import XkcdCNScraper
from shared.api_rest_client import APIRESTClient
from shared.http_client import HttpClient
from shared.types import LanguageCode
from shared.utils import chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


async def scrape_origin(
    from_: int,
    to_: int,
    chunk_size: int,
    http_client: HttpClient,
) -> list[XkcdORIGINFullScrapedData]:
    scraper = XkcdOriginScraper(client=http_client)

    comics_data = []

    with alive_bar(
        total=len(range(from_, to_ + 1)),
        title="Origin scraping...:",
        title_length=25,
        force_tty=True,
    ) as progress_bar:
        for chunk in chunks(lst=list(range(from_, to_ + 1)), n=chunk_size):
            try:
                async with asyncio.TaskGroup() as tg:
                    tasks = [
                        tg.create_task(scraper.fetch_one(number, progress_bar)) for number in chunk
                    ]
            except* Exception as errors:
                for e in errors.exceptions:
                    raise e
            else:
                [comics_data.append(task.result()) for task in tasks]

    logger.info("Successfully origin scraped.")

    return comics_data


async def upload_origin(
    api_client: APIRESTClient,
    origin_data: list[XkcdORIGINFullScrapedData],
    chunk_size: int,
) -> dict[int, int]:
    number_comic_id_map = {}

    with alive_bar(
        total=len(origin_data),
        title="Uploading origin...:",
        title_length=25,
    ) as progress_bar:
        for chunk in chunks(lst=origin_data, n=chunk_size):
            try:
                async with asyncio.TaskGroup() as tg:
                    tasks = [
                        tg.create_task(api_client.create_comic_with_image(data, progress_bar))
                        for data in chunk
                    ]
            except* Exception as errors:
                for e in errors.exceptions:
                    logger.error(e)
                    raise e
            else:
                for task in tasks:
                    number_comic_id_map |= task.result()

    logger.info("Successfully origin uploaded.")

    return number_comic_id_map


async def scrape_russian(
    from_: int,
    to_: int,
    chunk_size: int,
    http_client: HttpClient,
) -> list[XkcdTranslationData]:
    scraper = XkcdRUScraper(http_client)
    all_nums = await scraper.get_all_nums()

    nums = [num for num in all_nums if from_ <= num <= to_]

    ru_translation_data = []

    with alive_bar(
        total=len(nums),
        title="Xkcd RU scraping...:",
        title_length=25,
        force_tty=True,
    ) as progress_bar:
        for chunk in chunks(nums, chunk_size):
            try:
                async with asyncio.TaskGroup() as tg:
                    tasks = [
                        tg.create_task(scraper.fetch_one(number, progress_bar)) for number in chunk
                    ]
            except* Exception as errors:
                for e in errors.exceptions:
                    raise e
            else:
                for task in tasks:
                    ru_translation_data.append(task.result())

    return ru_translation_data


async def scrape_deutsch(
    from_: int,
    to_: int,
    chunk_size: int,
    http_client: HttpClient,
) -> list[XkcdTranslationData]:
    scraper = XkcdDEScraper(http_client)

    latest_num = await scraper.fetch_latest_number()

    nums = [n for n in range(from_, to_ + 1) if n <= latest_num]

    de_translation_data = []

    with alive_bar(
        title="Xkcd DE scraping...:",
        title_length=25,
        force_tty=True,
    ) as progress_bar:
        for chunk in chunks(nums, chunk_size):
            try:
                async with asyncio.TaskGroup() as tg:
                    tasks = [
                        tg.create_task(scraper.fetch_one(number, progress_bar)) for number in chunk
                    ]
            except* Exception as errors:
                for e in errors.exceptions:
                    raise e
            else:
                for task in tasks:
                    result = task.result()
                    if result:
                        de_translation_data.append(result)

    return de_translation_data


async def scrape_spanish(
    from_: int,
    to_: int,
    chunk_size: int,
    http_client: HttpClient,
) -> list[XkcdTranslationData]:
    scraper = XkcdESScraper(http_client)

    links = await scraper.fetch_all_links()

    es_translation_data = []

    with alive_bar(
        total=len(links),
        title="Xkcd ES scraping...:",
        title_length=25,
        force_tty=True,
    ) as progress_bar:
        for chunk in chunks(links, chunk_size):
            try:
                async with asyncio.TaskGroup() as tg:
                    tasks = [
                        tg.create_task(scraper.fetch_one(link, from_, to_, progress_bar))
                        for link in chunk
                    ]
            except* Exception as errors:
                for e in errors.exceptions:
                    raise e
            else:
                for task in tasks:
                    result = task.result()
                    if result:
                        es_translation_data.append(result)

    return es_translation_data


async def scrape_chinese(
    from_: int,
    to_: int,
    chunk_size: int,
    http_client: HttpClient,
) -> list[XkcdTranslationData]:
    scraper = XkcdCNScraper(http_client)

    links = [
        link
        for link in await scraper.fetch_all_links()
        if from_ <= int(str(link).split("=")[-1]) <= to_
    ]

    cn_translation_data = []

    with alive_bar(
        total=len(links),
        title="Xkcd CN scraping...:",
        title_length=25,
        force_tty=True,
    ) as progress_bar:
        for chunk in chunks(links, chunk_size):
            try:
                async with asyncio.TaskGroup() as tg:
                    tasks = [
                        tg.create_task(scraper.fetch_one(link, progress_bar)) for link in chunk
                    ]
            except* Exception as errors:
                for e in errors.exceptions:
                    raise e
            else:
                for task in tasks:
                    cn_translation_data.append(task.result())

    return cn_translation_data


async def upload_translations(
    number_comic_id_map: dict[int, int],
    translation_data: list[XkcdTranslationData],
    api_client: APIRESTClient,
    chunk_size: int,
    language: LanguageCode,
):
    with alive_bar(
        total=len(translation_data),
        title=f"Uploading translations...{language}:",
        title_length=25,
    ) as progress_bar:
        for chunk in chunks(lst=translation_data, n=chunk_size):
            try:
                async with asyncio.TaskGroup() as tg:
                    [
                        tg.create_task(
                            api_client.add_translation_with_image(
                                number_comic_id_map=number_comic_id_map,
                                data=data,
                                language=language,
                                progress_bar=progress_bar,
                            ),
                        )
                        for data in chunk
                    ]
            except* Exception as errors:
                for e in errors.exceptions:
                    logger.error(e)
                    raise e
            else:
                ...


async def main(from_: int = 1, to_: int | None = None, chunk_size: int = 100):
    async with HttpClient() as http_client:
        api_client = APIRESTClient(http_client)

        if await api_client.healthcheck():
            logger.info("Starting scraping...")
        else:
            return

        if not to_:
            to_ = await XkcdOriginScraper(client=http_client).fetch_latest_number()

        origin_data = await scrape_origin(from_, to_, chunk_size, http_client)

        number_comic_id_map = await upload_origin(api_client, origin_data, chunk_size)

        ru_translation_data = await scrape_russian(from_, to_, chunk_size, http_client)

        de_translation_data = await scrape_deutsch(from_, to_, chunk_size, http_client)

        es_translation_data = await scrape_spanish(from_, to_, chunk_size, http_client)

        cn_translations_data = await scrape_chinese(from_, to_, chunk_size, http_client)

        await upload_translations(
            number_comic_id_map,
            ru_translation_data,
            api_client,
            chunk_size,
            language=LanguageCode.RU,
        )

        await upload_translations(
            number_comic_id_map,
            de_translation_data,
            api_client,
            chunk_size,
            language=LanguageCode.DE,
        )

        await upload_translations(
            number_comic_id_map,
            es_translation_data,
            api_client,
            chunk_size,
            language=LanguageCode.ES,
        )

        await upload_translations(
            number_comic_id_map,
            cn_translations_data,
            api_client,
            chunk_size,
            language=LanguageCode.CN,
        )


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
