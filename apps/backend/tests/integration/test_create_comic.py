import datetime as dt
from collections.abc import AsyncGenerator

import pytest
from dishka import AsyncContainer

from backend.application.comic.commands import ComicCreateCommand
from backend.application.comic.responses import ComicResponseData
from backend.application.comic.services import ComicReader, CreateComicInteractor
from backend.domain.value_objects import ComicId


@pytest.fixture(scope="function")
async def comic_interactor(
    container: AsyncContainer,
) -> AsyncGenerator[CreateComicInteractor, None]:
    async with container() as request_container:
        yield await request_container.get(CreateComicInteractor)


@pytest.fixture(scope="function")
async def comic_reader(
    container: AsyncContainer,
) -> AsyncGenerator[ComicReader, None]:
    async with container() as request_container:
        yield await request_container.get(ComicReader)


async def test_create_comic_success(
    comic_interactor: CreateComicInteractor,
    comic_reader: ComicReader,
) -> None:
    request = ComicCreateCommand(
        number=1,
        title="SOME TITLE",
        publication_date=dt.date.fromisoformat("2019-12-04"),
        tooltip="SOME TOOLTIP",
        transcript="SOME TRANSCRIPT",
        xkcd_url="https://xkcd.com/1/",
        explain_url="https://explainxkcd.com/1",
        click_url=None,
        is_interactive=False,
        tag_ids=[],
        image_id=None,
    )

    assert await comic_interactor.execute(request) == ComicId(1)

    assert await comic_reader.get_by_id(ComicId(1)) == ComicResponseData(
        id=1,
        number=request.number,
        translation_id=1,
        title=request.title,
        tooltip=request.tooltip,
        publication_date=request.publication_date,
        xkcd_url=request.xkcd_url,
        explain_url=request.explain_url,
        click_url=request.click_url,
        is_interactive=request.is_interactive,
        tags=[],
        has_translations=[],
        image=None,
        translations=[],
    )
