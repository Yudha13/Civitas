"""Preserve village agent ordering for deterministic resume."""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("villages", sa.Column("agent_order", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("villages", "agent_order")
