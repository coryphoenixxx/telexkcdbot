import datetime as dt

from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.base_model import Base


class Comic(Base):
    issue_number: Mapped[int] = mapped_column(primary_key=True)
    publication_date: Mapped[dt.date] = mapped_column(nullable=False)
    reddit_url: Mapped[str] = mapped_column(nullable=True)
    explain_url: Mapped[str] = mapped_column(nullable=True)
    link_on_click: Mapped[str] = mapped_column(nullable=True)
    is_interactive: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_extra: Mapped[bool] = mapped_column(nullable=False, default=False)
