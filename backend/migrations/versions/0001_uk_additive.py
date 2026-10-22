"""Add UK-only tables; no changes to historical policy rows or currency columns."""
from alembic import op

from app.market import models  # noqa: F401
from app.models import Base

revision = "0001_uk_additive"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    for table in sorted(Base.metadata.tables.values(), key=lambda item: item.name):
        if table.name.startswith("uk_"):
            table.create(op.get_bind(), checkfirst=True)


def downgrade():
    # Operator must back up UK records before deliberately downgrading a live database.
    for table in sorted(Base.metadata.tables.values(), key=lambda item: item.name, reverse=True):
        if table.name.startswith("uk_"):
            table.drop(op.get_bind(), checkfirst=True)
