"""add_index_users_current_plan_id

Revision ID: 5dc8882d8c63
Revises: 8e25a887736f
Create Date: 2026-06-23 21:24:29.125276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5dc8882d8c63'
down_revision: Union[str, Sequence[str], None] = '8e25a887736f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(op.f('ix_users_current_plan_id'), 'users', ['current_plan_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_current_plan_id'), table_name='users')