"""Add war metrics to historical snapshots."""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("metrics", sa.Column("wars", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("metrics", sa.Column("war_casualties", sa.Integer(), nullable=False, server_default="0"))

def downgrade():
    op.drop_column("metrics", "war_casualties")
    op.drop_column("metrics", "wars")
