"""Add PENDING_MANUAL to report status enum.

Revision ID: 002_pending_manual
Revises: 001_initial
Create Date: 2026-11-07 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_pending_manual"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add PENDING_MANUAL to reports status check constraint / enum."""
    # Note: SQLAlchemy uses VARCHAR check constraint when native_enum=False,
    # or ALTER TYPE reportstatus ADD VALUE 'PENDING_MANUAL' on PostgreSQL.
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reportstatus') THEN
                    ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'PENDING_MANUAL';
                END IF;
            END$$;
            """
        )


def downgrade() -> None:
    """Downgrade schema."""
    pass
