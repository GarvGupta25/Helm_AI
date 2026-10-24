"""Add isolated draft intake, confirmed versions and frozen runs."""
from alembic import op

from app.journey.models import JourneyRun, JourneySession, ProfileVersion

revision = "0003_journey_intake"
down_revision = "0002_research"
branch_labels = None
depends_on = None


def upgrade():
    for model in (JourneySession, ProfileVersion, JourneyRun):
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    for model in (JourneyRun, ProfileVersion, JourneySession):
        model.__table__.drop(op.get_bind(), checkfirst=True)
