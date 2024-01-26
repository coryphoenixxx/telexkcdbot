from datetime import date

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class PkIdMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class TimestampMixin:
    created_at: Mapped[date] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[date] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )
