from dataclasses import dataclass

from backend.domain.value_objects import TagId, TagName


@dataclass(slots=True, kw_only=True)
class TagEntity:
    id: TagId
    name: TagName
    is_visible: bool
    from_explainxkcd: bool

    def set_name(self, name: str) -> None:
        self.name = TagName(name)

    @property
    def slug(self) -> str:
        return self.name.slug


@dataclass(slots=True, kw_only=True)
class NewTagEntity(TagEntity):
    id: TagId | None = None  # type: ignore[assignment]
