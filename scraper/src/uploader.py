import asyncio
from dataclasses import asdict

from src.dtos import AggregatedComicDataDTO, Images, XkcdPostApiDTO
from src.exceptions import UnexpectedStatusCodeError
from yarl import URL

from shared.http_client import HttpClient


class APIUploader:
    _API_URL = URL("http://localhost:8000/api/comics")
    _API_UPLOAD_IMAGE_URL = _API_URL.joinpath("upload_image")

    def __init__(
        self,
        client: HttpClient,
        queue: asyncio.Queue,
        threshold: int = 40,
    ):
        self._queue = queue
        self._client = client
        self._post_threshold = threshold
        self._listen_queue_task = None

    async def __aenter__(self):
        self.wait()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    def wait(self):
        self._listen_queue_task = asyncio.create_task(self._listen_queue())

    async def stop(self):
        await self._queue.put(None)
        await self._listen_queue_task

    async def _listen_queue(self):
        comics_for_post = []
        while True:
            comic: AggregatedComicDataDTO | None = await self._queue.get()
            if comic is None:
                await self.post_comics_to_api(comics_for_post)
                break

            comics_for_post.append(comic)

            if len(comics_for_post) == self._post_threshold:
                await self.post_comics_to_api(comics_for_post)
                comics_for_post.clear()

    async def post_comics_to_api(self, comics: list[AggregatedComicDataDTO]):
        try:
            async with asyncio.TaskGroup() as tg:
                [tg.create_task(self.post_comic_to_api(data=comic)) for comic in comics]
        except* Exception as errors:
            for e in errors.exceptions:
                raise e

    async def post_comic_to_api(
        self,
        data: AggregatedComicDataDTO,
    ):
        data = XkcdPostApiDTO(
            number=data.origin.number,
            publication_date=data.origin.publication_date,
            xkcd_url=data.origin.xkcd_url,
            title=data.origin.title,
            images=await self.upload_images(
                title=data.origin.title,
                number=data.origin.number,
                images=data.origin.images,
            ),
            is_interactive=data.origin.is_interactive,
            link_on_click=data.origin.link_on_click,
            tooltip=data.origin.tooltip,
            transcript=data.explain.transcript,
            tags=data.explain.tags,
        )

        async with self._client.safe_post(url=self._API_URL, json=data) as response:
            if response.status != 201:
                raise UnexpectedStatusCodeError(status=response.status)

    async def upload_images(
        self,
        title: str,
        number: int,
        images: Images,
    ) -> list[int]:
        image_ids = []

        for version, url in asdict(images).items():
            if url:
                async with self._client.safe_post(
                    url=self._API_UPLOAD_IMAGE_URL,
                    params={
                        "title": title,
                        "number": number,
                        "image_url": str(url),
                        "version": version,
                    },
                ) as response:
                    if response.status != 201:
                        raise UnexpectedStatusCodeError(status=response.status)

                    image_ids.append(int(await response.text()))

        return image_ids
