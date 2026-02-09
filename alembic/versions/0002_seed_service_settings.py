"""seed qe_service_setting"""

import sqlalchemy as sa

from alembic import op

revision = "0002_seed_service_settings"
down_revision = "0001_create_qe_core_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "INSERT INTO qe_service_setting (key, value) "
            "VALUES ('CONSENT_REVIEW_MONTHS', '6') "
            "ON CONFLICT (key) DO NOTHING"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM qe_service_setting WHERE key = 'CONSENT_REVIEW_MONTHS'")
    )
