import logging
from typing import BinaryIO

from aiohttp import ClientResponse
from yarl import URL

from scraper.dtos import XKCDPOSTData, XKCDFullScrapedData
from shared.http_client import HttpClient
from shared.types import (
    LanguageCode,
)


class APIRESTClient:
    _API_URL = URL("http://localhost:8000/api/")

    def __init__(self, client: HttpClient):
        self._client = client

    async def create_comic_with_image(self, data: XKCDFullScrapedData):
        images = []

        if data.image_url:
            image_id = (
                await self.upload_image(
                    title=data.title,
                    number=data.number,
                    image_url=data.image_url,
                )
            )["id"]
            images.append(image_id)

        await self.create_comic(
            comic=XKCDPOSTData(
                number=data.number,
                publication_date=data.publication_date,
                xkcd_url=data.xkcd_url,
                en_title=data.title,
                en_tooltip=data.tooltip,
                link_on_click=data.link_on_click,
                is_interactive=data.is_interactive,
                explain_url=data.explain_url,
                tags=data.tags,
                en_transcript=data.transcript,
                images=images,
            )
        )

    async def upload_image(
        self,
        title: str,
        number: int | None,
        language: LanguageCode = LanguageCode.EN,
        is_draft: bool = False,
        image_url: str | URL | None = None,
        image_file: BinaryIO | None = None,
    ) -> dict[str, int | str]:
        url = self._API_URL.joinpath("translations/upload_image")

        params = self._build_params(
            title=title,
            number=number,
            language=language,
            is_draft=is_draft,
            image_url=image_url,
        )

        async with self._client.safe_post(
            url=url,
            params=params,
            data={"image_file": image_file if image_file else ""},
        ) as response:  # type:ClientResponse
            if response.status == 201:
                return await response.json()
            else:
                error_json = await response.json()
                logging.error(
                    f"Uploading image №{number} is failed. Reason: {error_json['message']}"
                )

    async def create_comic(self, comic: XKCDPOSTData):
        url = self._API_URL.joinpath("comics")

        async with self._client.safe_post(url=url, json=comic) as response:  # type:ClientResponse
            if response.status == 201:
                return await response.json()
            else:
                error_json = await response.json()
                logging.error(
                    f"Creating comic №{comic.number} is failed. Reason: {error_json['message']}"
                )

    async def add_translation(self, translation): ...

    @staticmethod
    def _build_params(**kwargs) -> dict[str, int | float | str]:
        params = {}
        for name, value in kwargs.items():
            if value is not None:
                params[name] = str(value)

        return params
