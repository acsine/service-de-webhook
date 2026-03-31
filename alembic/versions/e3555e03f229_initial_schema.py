"""initial_schema

Revision ID: e3555e03f229
Revises: c42344d91d7e
Create Date: 2026-03-24 19:45:12.253899

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e3555e03f229'
down_revision: Union[str, None] = 'c42344d91d7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. tenants
    op.create_table(
        'tenants',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    # 2. users
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # 3. refresh_tokens
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )

    # 4. subscribers
    op.create_table(
        'subscribers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('callback_url', sa.Text(), nullable=False),
        sa.Column('secret_hmac_enc', sa.LargeBinary(), nullable=False),
        sa.Column('secret_hmac_key_id', sa.String(length=50), nullable=False),
        sa.Column('events', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('timeout_ms', sa.Integer(), nullable=False),
        sa.Column('rate_limit_per_min', sa.Integer(), nullable=False),
        sa.Column('failure_count', sa.Integer(), nullable=False),
        sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_subscribers_events', 'subscribers', ['events'], postgresql_using='gin')
    op.create_index('idx_subscribers_tenant_id', 'subscribers', ['tenant_id'])

    # 5. applications
    op.create_table(
        'applications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('client_id', sa.String(length=100), nullable=True),
        sa.Column('client_secret_enc', sa.LargeBinary(), nullable=True),
        sa.Column('subscriber_id', sa.UUID(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subscriber_id'], ['subscribers.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )

    # 6. events
    op.create_table(
        'events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('source_app', sa.String(length=100), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key')
    )
    op.create_index('idx_events_tenant_type', 'events', ['tenant_id', 'event_type'])
    op.create_index('idx_events_received_at', 'events', [sa.text('received_at DESC')])

    # 7. deliveries
    op.create_table(
        'deliveries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('event_id', sa.UUID(), nullable=False),
        sa.Column('subscriber_id', sa.UUID(), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('signature', sa.Text(), nullable=False),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subscriber_id'], ['subscribers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_deliveries_event_id', 'deliveries', ['event_id'])
    op.create_index('idx_deliveries_subscriber_id', 'deliveries', ['subscriber_id'])
    op.create_index('idx_deliveries_status_pending', 'deliveries', ['status'], postgresql_where=sa.text("status = 'pending'"))

    # 8. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.UUID(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_tenant_created', 'audit_logs', ['tenant_id', sa.text('created_at DESC')])

    # Materialized View
    op.execute("""
    CREATE MATERIALIZED VIEW delivery_stats_hourly AS
    SELECT
      date_trunc('hour', d.created_at)       AS hour,
      d.subscriber_id,
      s.tenant_id,
      COUNT(*)                               AS total,
      COUNT(*) FILTER (WHERE d.status = 'success') AS success_count,
      COUNT(*) FILTER (WHERE d.status = 'failed')  AS failure_count,
      AVG(d.duration_ms)                     AS avg_latency_ms,
      PERCENTILE_CONT(0.95) WITHIN GROUP
        (ORDER BY d.duration_ms)             AS p95_latency_ms,
      SUM(d.attempt_number - 1)              AS total_retries
    FROM deliveries d
    JOIN subscribers s ON s.id = d.subscriber_id
    GROUP BY 1, 2, 3;
    """)
    op.create_index('idx_stats_hour_sub', 'delivery_stats_hourly', ['hour', 'subscriber_id'], unique=True)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS delivery_stats_hourly CASCADE")
    op.drop_table('audit_logs')
    op.drop_table('deliveries')
    op.drop_table('events')
    op.drop_table('applications')
    op.drop_table('subscribers')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
    op.drop_table('tenants')
