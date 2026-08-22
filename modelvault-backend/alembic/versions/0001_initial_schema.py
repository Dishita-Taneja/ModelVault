"""Initial schema for ModelVault

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="Data Scientist"),
        sa.Column("department", sa.String(length=100), nullable=False, server_default="ML Engineering"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 2. models table
    op.create_table(
        "models",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("sensitivity_level", sa.String(length=50), nullable=False, server_default="MEDIUM"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_models_name", "models", ["name"], unique=False)
    op.create_index("ix_models_owner_id", "models", ["owner_id"], unique=False)

    # 3. access_events table
    op.create_table(
        "access_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("model_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False, server_default="API_GATEWAY"),
        sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=False),
        sa.ForeignKeyConstraint(["model_id"], ["models.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_access_events_user_id", "access_events", ["user_id"], unique=False)
    op.create_index("ix_access_events_model_id", "access_events", ["model_id"], unique=False)
    op.create_index("ix_access_events_action", "access_events", ["action"], unique=False)
    op.create_index("ix_access_events_timestamp", "access_events", ["timestamp"], unique=False)
    op.create_index("ix_access_events_user_model", "access_events", ["user_id", "model_id"], unique=False)
    op.create_index("ix_access_events_timestamp_desc", "access_events", [sa.text("timestamp DESC")], unique=False)

    # 4. anomaly_results table
    op.create_table(
        "anomaly_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("access_event_id", sa.Uuid(), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("flagged_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["access_event_id"], ["access_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("access_event_id"),
    )
    op.create_index("ix_anomaly_results_access_event_id", "anomaly_results", ["access_event_id"], unique=True)
    op.create_index("ix_anomaly_results_anomaly_score", "anomaly_results", ["anomaly_score"], unique=False)
    op.create_index("ix_anomaly_results_flagged_at", "anomaly_results", ["flagged_at"], unique=False)
    op.create_index("ix_anomaly_results_score_desc", "anomaly_results", [sa.text("anomaly_score DESC")], unique=False)


def downgrade() -> None:
    op.drop_table("anomaly_results")
    op.drop_table("access_events")
    op.drop_table("models")
    op.drop_table("users")
