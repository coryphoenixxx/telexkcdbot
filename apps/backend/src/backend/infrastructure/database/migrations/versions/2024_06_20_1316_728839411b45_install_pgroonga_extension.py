"""
install pgroonga extension

Revision ID: 728839411b45
Revises: d4e8b7248193
Create Date: 2024-06-20 13:16:21.847147

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "728839411b45"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("CREATE EXTENSION IF NOT EXISTS pgroonga"))


def downgrade() -> None:
    pass
