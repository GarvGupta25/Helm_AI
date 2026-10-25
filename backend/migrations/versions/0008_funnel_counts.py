"""Optional aggregate daily counts without visitor identities."""
from alembic import op

from app.journey.funnel import FunnelCount

revision='0008_funnel_counts'
down_revision='0007_wizard_otp'
branch_labels=None
depends_on=None


def upgrade():
    FunnelCount.__table__.create(op.get_bind(),checkfirst=True)


def downgrade():
    FunnelCount.__table__.drop(op.get_bind(),checkfirst=True)
