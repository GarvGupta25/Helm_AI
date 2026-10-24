"""Add synthetic case, contact, request, document and delivery boundaries."""
from alembic import op

from app.journey.case_models import MODELS

revision = "0004_journey_requests"
down_revision = "0003_journey_intake"
branch_labels = None
depends_on = None


def upgrade():
    for model in MODELS:
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    for model in reversed(MODELS):
        model.__table__.drop(op.get_bind(), checkfirst=True)
