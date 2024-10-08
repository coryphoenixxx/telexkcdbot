from copy import copy
from pathlib import Path
from typing import Any

from sqlalchemy import Row

from backend.application.comic.responses import (
    ComicCompactResponseData,
    ComicResponseData,
    TagResponseData,
    TranslationImageResponseData,
    TranslationResponseData,
)
from backend.domain.entities import (
    ComicEntity,
    ImageEntity,
    ImageLinkType,
    TagEntity,
    TranslationEntity,
    TranslationStatus,
)
from backend.domain.utils import cast_or_none
from backend.domain.value_objects import (
    ComicId,
    ImageId,
    IssueNumber,
    Language,
    PositiveInt,
    TagId,
    TagName,
    TempFileUUID,
    TranslationId,
    TranslationTitle,
)
from backend.infrastructure.database.models import (
    ComicModel,
    ImageModel,
    TagModel,
    TranslationModel,
)


class MappingError(Exception):
    _text: str

    @property
    def message(self) -> str:
        return self._text


def map_image_model_to_entity(image: ImageModel) -> ImageEntity:
    return ImageEntity(
        id=ImageId(image.image_id),
        temp_image_id=cast_or_none(TempFileUUID, image.temp_image_id),
        link_type=cast_or_none(ImageLinkType, image.link_type),
        link_id=cast_or_none(PositiveInt, image.link_id),
        original_path=cast_or_none(Path, image.original_path),
        converted_path=cast_or_none(Path, image.converted_path),
        converted_2x_path=cast_or_none(Path, image.converted_2x_path),
        is_deleted=image.is_deleted,
    )


def map_translation_model_to_entity(translation: TranslationModel) -> TranslationEntity:
    return TranslationEntity(
        id=TranslationId(translation.translation_id),
        comic_id=ComicId(translation.comic_id),
        title=TranslationTitle(translation.title),
        language=Language(translation.language),
        tooltip=translation.tooltip,
        transcript=translation.transcript,
        translator_comment=translation.translator_comment,
        source_url=translation.source_url,
        status=TranslationStatus(translation.status),
    )


def map_tag_model_to_entity(tag: TagModel) -> TagEntity:
    return TagEntity(
        id=TagId(tag.tag_id),
        name=TagName(tag.name),
        is_visible=tag.is_visible,
        from_explainxkcd=tag.from_explainxkcd,
    )


def map_comic_model_to_entity(comic: ComicModel) -> ComicEntity:
    original_translation = comic.translations[0]

    return ComicEntity(
        id=ComicId(comic.comic_id),
        number=IssueNumber(comic.number) if comic.number else None,
        publication_date=comic.publication_date,
        xkcd_url=original_translation.source_url,
        explain_url=comic.explain_url,
        click_url=comic.click_url,
        is_interactive=comic.is_interactive,
        original_translation_id=TranslationId(original_translation.translation_id),
        title=TranslationTitle(original_translation.title),
        tooltip=original_translation.tooltip,
        transcript=original_translation.transcript,
    )


def map_tag_model_to_data(tag: TagModel) -> TagResponseData:
    return TagResponseData(
        id=tag.tag_id,
        name=tag.name,
        is_visible=tag.is_visible,
        from_explainxkcd=tag.from_explainxkcd,
    )


def map_image_model_to_data(image: ImageModel) -> TranslationImageResponseData:
    if image.link_id is None:
        raise MappingError("Image was probably deleted.")
    return TranslationImageResponseData(
        id=image.image_id,
        translation_id=image.link_id,
        original=image.original_path,
        converted=image.converted_path,
        converted_2x=image.converted_2x_path,
    )


def map_translation_model_to_data(translation: TranslationModel) -> TranslationResponseData:
    return TranslationResponseData(
        id=translation.translation_id,
        comic_id=translation.comic_id,
        title=translation.title,
        language=Language(translation.language),
        tooltip=translation.tooltip,
        transcript=translation.transcript,
        translator_comment=translation.translator_comment,
        source_url=translation.source_url,
        images=[map_image_model_to_data(image) for image in translation.images],
        status=TranslationStatus(translation.status),
    )


def map_comic_model_to_data(comic: ComicModel) -> ComicResponseData:
    original_translation, translations = _separate_translations(copy(comic.translations))

    return ComicResponseData(
        id=comic.comic_id,
        number=comic.number,
        title=original_translation.title,
        translation_id=original_translation.translation_id,
        publication_date=comic.publication_date,
        tooltip=original_translation.tooltip,
        xkcd_url=original_translation.source_url,
        explain_url=comic.explain_url,
        click_url=comic.click_url,
        is_interactive=comic.is_interactive,
        tags=[map_tag_model_to_data(tag) for tag in comic.tags],
        images=[map_image_model_to_data(image) for image in original_translation.images],
        has_translations=[Language(tr.language) for tr in translations],
        translations=[map_translation_model_to_data(translation) for translation in translations],
    )


def map_row_to_compact_data(row: Row[Any]) -> ComicCompactResponseData:
    if row.converted_path:
        image_url = row.converted_path
    elif row.original_path:
        image_url = row.original_path
    else:
        image_url = None

    return ComicCompactResponseData(
        id=row.comic_id,
        number=row.number,
        publication_date=row.publication_date,
        title=row.title,
        image_url=image_url,
    )


def _separate_translations(
    translations: list[TranslationModel],
) -> tuple[TranslationModel, list[TranslationModel]]:
    for idx, tr in enumerate(translations):
        if tr.language == Language.EN:
            original_translation = translations.pop(idx)
            return original_translation, translations
    raise ValueError("Comic model hasn't english translations.")  # TODO: RepoError
