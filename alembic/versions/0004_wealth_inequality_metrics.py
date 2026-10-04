"""Add wealth inequality metrics to historical snapshots."""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("metrics", sa.Column("wealth_gini", sa.Float(), nullable=False, server_default="0"))
    op.add_column("metrics", sa.Column("top_10_wealth_share", sa.Float(), nullable=False, server_default="0"))


def downgrade():
    op.drop_column("metrics", "top_10_wealth_share")
    op.drop_column("metrics", "wealth_gini")
