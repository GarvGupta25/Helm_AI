"""Persist bounded OTP send windows without contact plaintext."""
from alembic import op

from app.journey.case_models import OtpWindow

revision = '0007_wizard_otp'
down_revision = '0006_member_demo'
branch_labels = None
depends_on = None


def upgrade():
    OtpWindow.__table__.create(op.get_bind(),checkfirst=True)


def downgrade():
    OtpWindow.__table__.drop(op.get_bind(),checkfirst=True)
