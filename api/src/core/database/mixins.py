from sqlalchemy.orm import Mapped, mapped_column


class PkIdMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
