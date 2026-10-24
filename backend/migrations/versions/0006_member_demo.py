"""Add isolated prototype member accounts, digested sessions and fictional policies."""
from alembic import op

from app.member_demo import MemberAccount, MemberPolicy, MemberSession

revision = '0006_member_demo'
down_revision = '0005_journey_access_exchange'
branch_labels = None
depends_on = None


def upgrade():
    for model in (MemberAccount, MemberSession, MemberPolicy):
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    for model in (MemberPolicy, MemberSession, MemberAccount):
        model.__table__.drop(op.get_bind(), checkfirst=True)
