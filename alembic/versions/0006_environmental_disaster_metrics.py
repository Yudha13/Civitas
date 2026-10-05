"""Add environmental disaster metric to historical snapshots."""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "metrics",
        sa.Column("environmental_disasters", sa.Integer(), nullable=False, server_default="0"),
    )

def downgrade():
    op.drop_column("metrics", "environmental_disasters")
