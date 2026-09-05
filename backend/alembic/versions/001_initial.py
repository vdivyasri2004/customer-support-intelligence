"""initial migration

Revision ID: 001
Revises: 
Create Date: 2025-01-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, index=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'datasets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False, server_default='upload'),
        sa.Column('original_filename', sa.String(255), nullable=True),
        sa.Column('row_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'tickets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dataset_id', sa.Integer(), sa.ForeignKey('datasets.id'), nullable=False, index=True),
        sa.Column('external_ticket_id', sa.String(100), nullable=True, index=True),
        sa.Column('customer_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('priority', sa.String(50), nullable=True, index=True),
        sa.Column('status', sa.String(50), nullable=True, index=True),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('channel', sa.String(50), nullable=True),
        sa.Column('agent', sa.String(100), nullable=True, index=True),
        sa.Column('first_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_time_minutes', sa.Float(), nullable=True),
        sa.Column('resolution_time_minutes', sa.Float(), nullable=True),
        sa.Column('satisfaction_score', sa.Float(), nullable=True),
        sa.Column('sentiment', sa.String(20), nullable=True, index=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('sla_met', sa.Boolean(), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
    )

    op.create_table(
        'analyses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('dataset_id', sa.Integer(), sa.ForeignKey('datasets.id'), nullable=False, index=True),
        sa.Column('analysis_name', sa.String(255), nullable=False),
        sa.Column('summary_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('idx_dataset_category', 'tickets', ['dataset_id', 'category'])
    op.create_index('idx_dataset_status', 'tickets', ['dataset_id', 'status'])
    op.create_index('idx_dataset_priority', 'tickets', ['dataset_id', 'priority'])


def downgrade() -> None:
    op.drop_table('analyses')
    op.drop_table('tickets')
    op.drop_table('datasets')
    op.drop_table('users')
