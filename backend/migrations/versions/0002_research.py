"""Add isolated synthetic catalogue and capability-scoped research state."""
from alembic import op

from app.research.models import ResearchRecord, ResearchSession

revision = "0002_research"
down_revision = "0001_uk_additive"
branch_labels = None
depends_on = None


def upgrade():
    ResearchRecord.__table__.create(op.get_bind(), checkfirst=True)
    ResearchSession.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    ResearchSession.__table__.drop(op.get_bind(), checkfirst=True)
    ResearchRecord.__table__.drop(op.get_bind(), checkfirst=True)
