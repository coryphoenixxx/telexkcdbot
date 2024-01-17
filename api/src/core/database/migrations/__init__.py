__all__ = [
    "ComicModel",
    "ComicTagAssociation",
    "TagModel",
    "TranslationModel",
    "TranslationImageModel",
]

from src.app.comics.models import ComicModel, ComicTagAssociation, TagModel
from src.app.images.models import TranslationImageModel
from src.app.translations.models import TranslationModel
