"""Alembic script template."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema — all tables created by SQLAlchemy models."""
    pass


def downgrade() -> None:
    pass
