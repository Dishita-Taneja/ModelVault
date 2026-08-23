"""add performance composite indexes

Revision ID: 002_add_performance_composite_indexes
Revises: 001_initial_schema
Create Date: 2026-08-23 13:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_performance_composite_indexes'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite indexes on normalized_events
    op.create_index('idx_normalized_user_time', 'normalized_events', ['user_id', 'event_time_reconciled'], unique=False)
    op.create_index('idx_normalized_model_time', 'normalized_events', ['model_id', 'event_time_reconciled'], unique=False)
    op.create_index('idx_normalized_source_time', 'normalized_events', ['source', 'event_time_reconciled'], unique=False)

    # Composite indexes on suspicious_events
    op.create_index('idx_suspicious_risk_severity', 'suspicious_events', ['risk_score', 'severity'], unique=False)
    op.create_index('idx_suspicious_user_time', 'suspicious_events', ['user_id', 'timestamp'], unique=False)
    op.create_index('idx_suspicious_model_time', 'suspicious_events', ['model_id', 'timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_suspicious_model_time', table_name='suspicious_events')
    op.drop_index('idx_suspicious_user_time', table_name='suspicious_events')
    op.drop_index('idx_suspicious_risk_severity', table_name='suspicious_events')

    op.drop_index('idx_normalized_source_time', table_name='normalized_events')
    op.drop_index('idx_normalized_model_time', table_name='normalized_events')
    op.drop_index('idx_normalized_user_time', table_name='normalized_events')
