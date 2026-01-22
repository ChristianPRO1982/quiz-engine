"""create qe core tables"""

import sqlalchemy as sa

from alembic import op

revision = "0001_create_qe_core_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "qe_user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qe_user")),
        sa.UniqueConstraint("subject", name=op.f("uq_qe_user_subject")),
    )

    op.create_table(
        "qe_service_setting",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_qe_service_setting")),
    )

    op.create_table(
        "qe_quiz",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["qe_user.id"],
            name=op.f("fk_qe_quiz_created_by_user_id_qe_user"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qe_quiz")),
    )

    op.create_table(
        "qe_session",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_code", sa.String(length=12), nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=True),
        sa.Column("host_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "state",
            sa.Enum("LOBBY", "RUNNING", "ENDED", name="qe_session_state"),
            server_default="LOBBY",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["host_user_id"],
            ["qe_user.id"],
            name=op.f("fk_qe_session_host_user_id_qe_user"),
        ),
        sa.ForeignKeyConstraint(
            ["quiz_id"],
            ["qe_quiz.id"],
            name=op.f("fk_qe_session_quiz_id_qe_quiz"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qe_session")),
        sa.UniqueConstraint("session_code", name=op.f("uq_qe_session_session_code")),
    )

    op.create_table(
        "qe_user_role",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "moderator", name="qe_user_role"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["qe_user.id"],
            name=op.f("fk_qe_user_role_user_id_qe_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qe_user_role")),
        sa.UniqueConstraint("user_id", "role", name=op.f("uq_qe_user_role_user_id")),
    )

    op.create_table(
        "qe_consent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "scope",
            sa.Enum("pseudo", "history", "email", name="qe_consent_scope"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("granted", "revoked", name="qe_consent_status"),
            nullable=False,
        ),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["qe_user.id"],
            name=op.f("fk_qe_consent_user_id_qe_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qe_consent")),
        sa.UniqueConstraint("user_id", "scope", name=op.f("uq_qe_consent_user_id")),
    )

    op.create_table(
        "qe_consent_audit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "scope",
            sa.Enum("pseudo", "history", "email", name="qe_consent_scope"),
            nullable=False,
        ),
        sa.Column(
            "action",
            sa.Enum(
                "granted",
                "revoked",
                "expired",
                "revalidated",
                name="qe_consent_action",
            ),
            nullable=False,
        ),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["qe_user.id"],
            name=op.f("fk_qe_consent_audit_user_id_qe_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qe_consent_audit")),
    )

    op.create_table(
        "qe_player",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("player_code", sa.String(length=64), nullable=False),
        sa.Column("nickname", sa.String(length=64), nullable=False),
        sa.Column(
            "is_guest",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["qe_session.id"],
            name=op.f("fk_qe_player_session_id_qe_session"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["qe_user.id"],
            name=op.f("fk_qe_player_user_id_qe_user"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qe_player")),
        sa.UniqueConstraint("player_code", name=op.f("uq_qe_player_player_code")),
    )
    op.create_index(
        "ix_qe_player_session_id", "qe_player", ["session_id"], unique=False
    )

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


def downgrade() -> None:
    op.drop_index("ix_qe_question_result_session_id", table_name="qe_question_result")
    op.drop_table("qe_question_result")
    op.drop_index("ix_qe_answer_session_id", table_name="qe_answer")
    op.drop_table("qe_answer")
    op.drop_index("ix_qe_player_session_id", table_name="qe_player")
    op.drop_table("qe_player")
    op.drop_table("qe_consent_audit")
    op.drop_table("qe_consent")
    op.drop_table("qe_user_role")
    op.drop_table("qe_session")
    op.drop_table("qe_quiz")
    op.drop_table("qe_service_setting")
    op.drop_table("qe_user")
