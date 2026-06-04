"""baseline current WFM schema

Revision ID: 20260526_0001
Revises:
Create Date: 2026-05-26
"""

from alembic import op

from app.models.integration_settings import Base
import app.models.wfm  # noqa: F401

revision = "20260526_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    # Baseline migration is intentionally non-destructive: existing project data
    # must not be dropped by an accidental rollback.
    pass
