"""Add deterministic resume state to simulations."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("simulations", sa.Column("initial_population", sa.Integer(), nullable=True))
    op.add_column("simulations", sa.Column("rng_state", sa.Text(), nullable=True))
    op.execute("UPDATE simulations SET initial_population = population WHERE initial_population IS NULL")
    op.alter_column("simulations", "initial_population", nullable=False)


def downgrade():
    op.drop_column("simulations", "rng_state")
    op.drop_column("simulations", "initial_population")
