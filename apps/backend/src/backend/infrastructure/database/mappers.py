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
from backend.domain.entities.image import ImageMeta
from backend.domain.utils import cast_or_none, value_or_none
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
from backend.domain.value_objects.image_file import ImageFormat
from backend.infrastructure.database.models import (
    ComicModel,
    ImageModel,
    TagModel,
    TranslationModel,
)
from backend.infrastructure.database.repositories import RepoError


class MappingError(Exception):
    _text: str

    @property
    def message(self) -> str:
        return self._text


def map_image_meta_json_to_image_meta_ds(meta: dict[str, Any]) -> ImageMeta:
    return ImageMeta(
        format=ImageFormat(meta["format"]),
        size=meta["size"],
        dimensions=tuple(meta["dimensions"]),
    )


def map_image_model_to_entity(image: ImageModel) -> ImageEntity:
    return ImageEntity(
        id=ImageId(image.image_id),
        temp_image_id=cast_or_none(TempFileUUID, image.temp_image_id),
        entity_type=cast_or_none(ImageLinkType, image.entity_type),
        entity_id=cast_or_none(PositiveInt, image.entity_id),
        image_path=cast_or_none(Path, image.image_path),
        meta=map_image_meta_json_to_image_meta_ds(image.meta),
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
    if image.entity_id is None:
        raise MappingError("Image was probably deleted.")
    if image.image_path is None:
        raise MappingError("Image was probably is not created.")

    return TranslationImageResponseData(
        id=image.image_id,
        translation_id=image.entity_id,
        image_path=image.image_path,
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
        image=map_image_model_to_data(translation.image) if translation.image else None,
        status=TranslationStatus(translation.status),
    )


def map_comic_model_to_data(comic: ComicModel) -> ComicResponseData:
    original_translation, translations = None, []

    for translation in comic.translations:
        if translation.language == Language.EN:
            original_translation = translation
        else:
            translations.append(translation)

    if original_translation is None:
        raise RepoError("Comic model hasn't english translations.")

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
        image=(
            map_image_model_to_data(original_translation.image)
            if original_translation.image
            else None
        ),
        has_translations=[Language(tr.language) for tr in translations],
        translations=[map_translation_model_to_data(translation) for translation in translations],
    )


def map_row_to_compact_data(row: Row[Any]) -> ComicCompactResponseData:
    return ComicCompactResponseData(
        id=row.comic_id,
        number=row.number,
        publication_date=row.publication_date,
        title=row.title,
        image_url=row.image_path,
    )


def map_image_entity_to_dict(image: ImageEntity, with_id: bool = False) -> dict[str, Any]:
    d = {
        "temp_image_id": value_or_none(image.temp_image_id),
        "entity_type": image.entity_type,
        "entity_id": value_or_none(image.entity_id),
        "image_path": cast_or_none(str, image.image_path),
        "meta": image.meta.to_dict(),
        "is_deleted": image.is_deleted,
    }

    if with_id:
        d["image_id"] = value_or_none(image.id)

    return d


def map_translation_entity_to_dict(translation: TranslationEntity) -> dict[str, Any]:
    return {
        "comic_id": translation.comic_id.value,
        "title": translation.title.value,
        "language": translation.language,
        "tooltip": translation.tooltip,
        "transcript": translation.transcript,
        "translator_comment": translation.translator_comment,
        "source_url": translation.source_url,
        "status": translation.status,
        "searchable_text": translation.searchable_text,
    }


def map_tag_entity_to_dict(tag: TagEntity) -> dict[str, Any]:
    return {
        "name": tag.name.value,
        "slug": tag.name.slug,
        "is_visible": tag.is_visible,
        "from_explainxkcd": tag.from_explainxkcd,
    }


def map_comic_entity_do_dicts(comic: ComicEntity) -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        {
            "number": value_or_none(comic.number),
            "slug": comic.slug,
            "publication_date": comic.publication_date,
            "explain_url": comic.explain_url,
            "click_url": comic.click_url,
            "is_interactive": comic.is_interactive,
        },
        {
            "title": comic.title.value,
            "language": Language.EN,
            "tooltip": comic.tooltip,
            "transcript": comic.transcript,
            "source_url": comic.xkcd_url,
            "status": TranslationStatus.PUBLISHED,
            "searchable_text": comic.searchable_text,
        },
    )
