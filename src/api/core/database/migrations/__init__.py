__all__ = [
    "ComicModel",
    "ComicTagAssociation",
    "TagModel",
    "TranslationModel",
    "TranslationImageModel",
]

from api.application.comics.models import ComicModel, ComicTagAssociation, TagModel
from api.application.images.models import TranslationImageModel
from api.application.translations.models import TranslationModel
