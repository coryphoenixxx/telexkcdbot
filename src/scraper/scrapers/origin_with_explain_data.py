import asyncio

from rich.progress import Progress

from scraper.dtos import (
    XkcdExplanationScrapedBaseData,
    XkcdOriginScrapedData,
    XkcdOriginWithExplainScrapedData,
)
from scraper.pbar import ProgressBar
from scraper.scrapers import XkcdOriginScraper
from scraper.scrapers.explain import XkcdExplainScraper
from scraper.types import LimitParams


class XkcdOriginWithExplainDataScraper:
    def __init__(
        self,
        origin_scraper: XkcdOriginScraper,
        explain_scraper: XkcdExplainScraper,
    ):
        self.origin_scraper = origin_scraper
        self.explain_scraper = explain_scraper

    async def fetch_one(
        self,
        number: int,
        pbar: ProgressBar | None = None,
    ) -> XkcdOriginWithExplainScrapedData | None:
        try:
            async with asyncio.TaskGroup() as tg:
                fetch_origin_task = tg.create_task(self.origin_scraper.fetch_one(number))
                fetch_explain_task = tg.create_task(self.explain_scraper.fetch_one(number))
        except* Exception as errors:
            for exc in errors.exceptions:
                raise exc
        else:
            origin_data, explain_data = fetch_origin_task.result(), fetch_explain_task.result()

            if not origin_data:
                return None

            data = self._combine(origin_data, explain_data)

            if pbar:
                pbar.advance()

            return data

    async def fetch_many(
        self,
        limits: LimitParams,
        progress: Progress,
    ) -> list[XkcdOriginWithExplainScrapedData]:
        async with asyncio.TaskGroup() as tg:
            fetch_origin_task = tg.create_task(self.origin_scraper.fetch_many(limits, progress))
            fetch_explain_task = tg.create_task(self.explain_scraper.fetch_many(limits, progress))

        origin_data_list, explain_data_list = (
            fetch_origin_task.result(),
            fetch_explain_task.result(),
        )

        data = []

        for origin_data, explain_data in zip(
            sorted(origin_data_list, key=lambda d: d.number),
            sorted(explain_data_list, key=lambda d: d.number),
            strict=True,
        ):
            data.append(self._combine(origin_data, explain_data))

        return data

    def _combine(
        self,
        origin_data: XkcdOriginScrapedData,
        explain_data: XkcdExplanationScrapedBaseData,
    ) -> XkcdOriginWithExplainScrapedData:
        return XkcdOriginWithExplainScrapedData(
            number=origin_data.number,
            publication_date=origin_data.publication_date,
            xkcd_url=origin_data.xkcd_url,
            title=origin_data.title,
            tooltip=origin_data.tooltip,
            link_on_click=origin_data.link_on_click,
            is_interactive=origin_data.is_interactive,
            image_url=origin_data.image_url,
            explain_url=explain_data.explain_url if explain_data else None,
            tags=explain_data.tags if explain_data else [],
            transcript_raw=explain_data.transcript_raw if explain_data else "",
        )
