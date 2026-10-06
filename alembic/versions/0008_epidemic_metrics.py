"""Add epidemic state and historical metrics."""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("agents", sa.Column("disease_days", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("agents", sa.Column("immune", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("metrics", sa.Column("epidemics", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("metrics", sa.Column("epidemic_infections", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("metrics", sa.Column("epidemic_deaths", sa.Integer(), nullable=False, server_default="0"))

def downgrade():
    op.drop_column("metrics", "epidemic_deaths")
    op.drop_column("metrics", "epidemic_infections")
    op.drop_column("metrics", "epidemics")
    op.drop_column("agents", "immune")
    op.drop_column("agents", "disease_days")
