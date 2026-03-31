"""add target_app_id to events

Revision ID: 0f98a0ba4dac
Revises: 6247453db0da
Create Date: 2026-03-25 15:44:32.764476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0f98a0ba4dac'
down_revision: Union[str, None] = '6247453db0da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('events', sa.Column('target_app_id', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('events', 'target_app_id')

    # ### end Alembic commands ###
