import logging
from pathlib import Path

from aiohttp import ClientResponse  # noqa: F401
from scraper.dtos import (
    XkcdOriginUploadData,
    XkcdOriginWithExplainScrapedData,
    XkcdTranslationData,
    XkcdTranslationUploadData,
)
from yarl import URL

from shared.api_rest_client.exceptions import APIServerError
from shared.http_client import AsyncHttpClient
from shared.my_types import Order

logger = logging.getLogger(__name__)


class APIRESTClient:
    def __init__(
        self,
        base_url: str,
        http_client: AsyncHttpClient = AsyncHttpClient(),
    ):
        self._base_url = URL(base_url)
        self._http_client = http_client

    async def healthcheck(self) -> None:
        url = self._base_url / "healthcheck"

        async with self._http_client.safe_get(url) as response:
            if response.status != 200:
                raise APIServerError

    async def login(self, username: str, password: str):
        url = self._base_url / "users/login"

        async with self._http_client.safe_post(
            url=url,
            json={
                "username": username,
                "raw_password": password,
            },
        ) as response:  # type: ClientResponse
            if response.status != 200:
                raise APIServerError

            session = self._http_client.get_session_by_host(host=URL(self._base_url).host)
            session.cookie_jar.update_cookies({"session_id": response.cookies["session_id"].value})

    async def create_comic_with_image(
        self,
        data: XkcdOriginWithExplainScrapedData,
    ) -> dict[int, int]:
        image_ids = []

        if data.image_url:
            image_id = (
                await self.upload_image(
                    title=data.title,
                    number=data.number,
                    language="EN",
                    image_url=data.image_url,
                )
            )["id"]
            image_ids.append(image_id)

        comic_id = await self.create_comic(
            comic=XkcdOriginUploadData(
                number=data.number,
                publication_date=data.publication_date,
                xkcd_url=data.xkcd_url,
                title=data.title,
                tooltip=data.tooltip,
                click_url=data.click_url,
                is_interactive=data.is_interactive,
                explain_url=data.explain_url,
                tags=data.tags,
                raw_transcript=data.raw_transcript,
                image_ids=image_ids,
            ),
        )

        return {data.number: comic_id}

    async def upload_image(
        self,
        title: str,
        number: int | None,
        language: str,
        is_draft: bool = False,
        image_url: str | URL | None = None,
        image_path: Path | None = None,
    ) -> dict[str, int | str]:
        url = self._base_url / "translations/upload_image"

        params = self._build_params(
            title=title,
            number=number,
            language=language,
            is_draft=is_draft,
            image_url=image_url,
        )

        async with self._http_client.safe_post(
            url=url,
            params=params,
            data={"image_file": open(image_path, "rb") if image_path else ""},
        ) as response:  # type:ClientResponse
            if response.status != 201:
                raise APIServerError
            else:
                return await response.json()

    async def create_comic(self, comic: XkcdOriginUploadData) -> int:
        url = self._base_url / "comics"

        async with self._http_client.safe_post(
            url=url,
            json=comic,
        ) as response:  # type:ClientResponse
            if response.status == 201:
                return (await response.json())["id"]
            else:
                raise APIServerError

    async def add_translation_with_image(
        self,
        data: XkcdTranslationData,
        number_comic_id_map: dict[int, int],
    ):
        comic_id = number_comic_id_map[data.number]

        url = self._base_url / f"comics/{comic_id}/translations"

        image_ids = []

        if data.image:
            image_id = (
                await self.upload_image(
                    title=data.title,
                    number=data.number,
                    language=data.language,
                    image_url=data.image if isinstance(data.image, URL) else None,
                    image_path=data.image if isinstance(data.image, Path) else None,
                )
            )["id"]
            image_ids.append(image_id)

        translation = XkcdTranslationUploadData(
            comic_id=comic_id,
            title=data.title,
            language=data.language,
            tooltip=data.tooltip,
            raw_transcript=data.raw_transcript,
            translator_comment=data.translator_comment,
            source_url=data.source_url,
            image_ids=image_ids,
        )

        async with self._http_client.safe_post(
            url=url,
            json=translation,
        ) as response:  # type:ClientResponse
            if response.status == 201:
                return (await response.json())["id"]
            else:
                raise APIServerError()

    async def get_comic_by_number(self, number: int, languages: list[str] | None = None):
        url = self._base_url / f"comics/{number}"

        params = [("lg", lang) for lang in languages] if languages else None

        async with self._http_client.safe_get(url, params=params) as response:
            if response.status == 200:
                return await response.json()

    async def get_comics(
        self,
        limit: int | None = None,
        page: int | None = None,
        order: Order | None = Order.ASC,
        date_from: str | None = None,
        date_to: str | None = None,
    ):
        # TODO: Set limits
        url = self._base_url / "comics"

        params = self._build_params(
            limit=limit,
            page=page,
            order=order,
            date_from=date_from,
            date_to=date_to,
        )

        async with self._http_client.safe_get(
            url=url,
            params=params,
        ) as response:
            comics = await response.json()

        return comics

    def _build_params(self, **kwargs) -> dict[str, int | float | str]:
        params = {}
        for name, value in kwargs.items():
            if value is not None:
                params[name] = str(value)

        return params

    async def stop(self):
        await self._http_client.close_all_sessions()
