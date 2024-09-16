import datetime as dt
from collections.abc import Generator

import pytest
from dishka import AsyncContainer

from backend.application.comic.dtos import ComicRequestDTO, ComicResponseDTO, TagResponseDTO
from backend.application.comic.services import ComicWriteService
from backend.core.value_objects import ComicID, IssueNumber, TagID, TagName, TranslationID


@pytest.fixture(scope="function")
async def comic_write_service(
    container: AsyncContainer,
) -> Generator[ComicWriteService, None, None]:
    async with container() as request_container:
        yield await request_container.get(ComicWriteService)


async def test_create_comic_success(comic_write_service: ComicWriteService) -> None:
    request = ComicRequestDTO(
        number=IssueNumber(1),
        title="SOME TITLE",
        publication_date=dt.date.fromisoformat("2019-12-04"),
        tooltip="SOME TOOLTIP",
        raw_transcript="SOME TRANSCRIPT",
        xkcd_url="https://xkcd.com/1/",
        explain_url="https://explainxkcd.com/1",
        click_url=None,
        is_interactive=False,
        tags=[TagName("Tag 1"), TagName("Tag 2")],
        temp_image_id=None,
    )

    assert await comic_write_service.create(request) == ComicResponseDTO(
        id=ComicID(value=1),
        number=request.number,
        title=request.title,
        tooltip=request.tooltip,
        publication_date=request.publication_date,
        xkcd_url=request.xkcd_url,
        explain_url=request.explain_url,
        click_url=request.click_url,
        is_interactive=request.is_interactive,
        tags=[
            TagResponseDTO(id=TagID(1), name=request.tags[0], is_blacklisted=False),
            TagResponseDTO(id=TagID(2), name=request.tags[1], is_blacklisted=False),
        ],
        has_translations=[],
        translation_id=TranslationID(value=1),
        image=None,
        translations=[],
    )
