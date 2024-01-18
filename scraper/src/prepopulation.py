import asyncio
import logging
from dataclasses import asdict

import aiohttp
import uvloop
from src.dtos import Images, XkcdCompleteDTO, XkcdOriginDTO
from src.scrapers.explain_xkcd_scraper import ExplainXkcdScraper
from src.scrapers.xkcd_origin import XkcdOriginScraper
from src.utils import get_session


async def upload_images(
    api_session: aiohttp.ClientSession,
    title: str,
    issue_number: int,
    images: Images,
) -> list[int]:
    results = []
    for version, url in asdict(images).items():
        if url:
            async with api_session.post(
                url="http://localhost:8000/api/comics/upload_image",
                params={
                    "title": title,
                    "issue_number": issue_number,
                    "image_url": url,
                    "version": version,
                },
            ) as response:
                status = response.status
                if status == 201:
                    image_id: int = int(await response.text())
                    results.append(image_id)
                else:
                    logging.error(
                        f"API for {url} responded {status}. Response: {await response.json()}",
                    )

    return results


async def post_comic_to_api(
    api_session: aiohttp.ClientSession,
    explain_session: aiohttp.ClientSession,
    comic_data: XkcdOriginDTO,
):
    upload_images_task = asyncio.create_task(
        upload_images(
            api_session=api_session,
            title=comic_data.title,
            issue_number=comic_data.issue_number,
            images=comic_data.images,
        ),
    )

    get_tags_task = asyncio.create_task(
        ExplainXkcdScraper(session=explain_session).fetch_tags(comic_data.issue_number),
    )

    data = XkcdCompleteDTO(
        issue_number=comic_data.issue_number,
        publication_date=comic_data.publication_date,
        xkcd_url=comic_data.xkcd_url,
        title=comic_data.title,
        images=await upload_images_task,
        is_interactive=comic_data.is_interactive,
        link_on_click=comic_data.link_on_click,
        tooltip=comic_data.tooltip,
        news=comic_data.news,
        tags=await get_tags_task,
    )

    async with await api_session.post(
        url="http://localhost:8000/api/comics",
        json=asdict(data),
    ) as response:
        return response.status, await response.json()


async def post_comics_to_api(comics: list[XkcdOriginDTO]):
    async with (
        aiohttp.ClientSession() as api_session,
        get_session() as explain_session,
        asyncio.TaskGroup() as tg,
    ):
        tasks = [
            tg.create_task(
                post_comic_to_api(
                    api_session=api_session,
                    explain_session=explain_session,
                    comic_data=comic,
                ),
            )
            for comic in comics
        ]

    for t in tasks:
        status, api_response_json = t.result()
        if status != 201:
            logging.error(f"API: {api_response_json}")


async def queue_reader(q: asyncio.Queue):
    comic_list_for_post = []
    while True:
        comic: XkcdOriginDTO = await q.get()
        if comic is None:
            await post_comics_to_api(comic_list_for_post)
            break

        comic_list_for_post.append(comic)

        if len(comic_list_for_post) == 25:
            await post_comics_to_api(comic_list_for_post)
            comic_list_for_post.clear()


async def main():
    q = asyncio.Queue()
    result_task = asyncio.create_task(queue_reader(q))
    await XkcdOriginScraper(q=q).fetch_many()
    await q.put(None)
    await result_task


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
