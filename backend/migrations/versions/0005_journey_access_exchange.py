"""Only one dashboard session may consume a magic-link grant."""
import sqlalchemy as sa
from alembic import op

revision = "0005_journey_access_exchange"
down_revision = "0004_journey_requests"
branch_labels = None
depends_on = None


def upgrade():
    if "parent_id" not in {c['name'] for c in sa.inspect(op.get_bind()).get_columns('journey_access_grant')}:
        with op.batch_alter_table('journey_access_grant') as batch:
            batch.add_column(sa.Column('parent_id', sa.String(36), nullable=True))
            batch.create_foreign_key('fk_journey_grant_parent', 'journey_access_grant', ['parent_id'], ['id'])
            batch.create_unique_constraint('uq_journey_grant_parent', ['parent_id'])


def downgrade():
    with op.batch_alter_table('journey_access_grant') as batch:
        batch.drop_column('parent_id')
