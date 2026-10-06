"""Add ideology state and historical metrics."""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("agents", sa.Column("ideology", sa.String(length=32), nullable=False, server_default="traditional"))
    op.add_column("agents", sa.Column("ideology_commitment", sa.Float(), nullable=False, server_default="0.25"))
    op.add_column("metrics", sa.Column("ideology_diversity", sa.Float(), nullable=False, server_default="0"))
    op.add_column("metrics", sa.Column("dominant_ideology_share", sa.Float(), nullable=False, server_default="0"))
    op.add_column("metrics", sa.Column("ideology_shifts", sa.Integer(), nullable=False, server_default="0"))

def downgrade():
    op.drop_column("metrics", "ideology_shifts")
    op.drop_column("metrics", "dominant_ideology_share")
    op.drop_column("metrics", "ideology_diversity")
    op.drop_column("agents", "ideology_commitment")
    op.drop_column("agents", "ideology")
