"""replace qe_answer and qe_question_result with qe_stage_* tables"""

import sqlalchemy as sa

from alembic import op

revision = "0003_replace_answer_result_with_stage_event_outcome"
down_revision = "0002_seed_service_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "qe_stage_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.String(length=64), nullable=False),
        sa.Column("stage_index", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["qe_session.id"],
            name=op.f("fk_qe_stage_event_session_id_qe_session"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qe_stage_event")),
    )
    op.create_index(
        "ix_qe_stage_event_session_id",
        "qe_stage_event",
        ["session_id"],
        unique=False,
    )

    op.create_table(
        "qe_stage_outcome",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.String(length=64), nullable=False),
        sa.Column("stage_index", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["qe_session.id"],
            name=op.f("fk_qe_stage_outcome_session_id_qe_session"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qe_stage_outcome")),
    )
    op.create_index(
        "ix_qe_stage_outcome_session_id",
        "qe_stage_outcome",
        ["session_id"],
        unique=False,
    )

    op.drop_index("ix_qe_question_result_session_id", table_name="qe_question_result")
    op.drop_table("qe_question_result")
    op.drop_index("ix_qe_answer_session_id", table_name="qe_answer")
    op.drop_table("qe_answer")


def downgrade() -> None:
    op.create_table(
        "qe_answer",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["qe_player.id"],
            name=op.f("fk_qe_answer_player_id_qe_player"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["qe_session.id"],
            name=op.f("fk_qe_answer_session_id_qe_session"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qe_answer")),
    )
    op.create_index(
        "ix_qe_answer_session_id", "qe_answer", ["session_id"], unique=False
    )

    op.create_table(
        "qe_question_result",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["qe_session.id"],
            name=op.f("fk_qe_question_result_session_id_qe_session"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qe_question_result")),
    )
    op.create_index(
        "ix_qe_question_result_session_id",
        "qe_question_result",
        ["session_id"],
        unique=False,
    )

    op.drop_index("ix_qe_stage_outcome_session_id", table_name="qe_stage_outcome")
    op.drop_table("qe_stage_outcome")
    op.drop_index("ix_qe_stage_event_session_id", table_name="qe_stage_event")
    op.drop_table("qe_stage_event")
