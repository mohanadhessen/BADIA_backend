"""Restore the payment gateway token column used by the payment model.

Revision ID: 4f3c2b9a1d70
Revises: 0dcecf64cb51
Create Date: 2026-10-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4f3c2b9a1d70"
down_revision: Union[str, Sequence[str], None] = "0dcecf64cb51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("gateway_token", sa.String(length=255), nullable=True))
    op.create_index("ix_payments_gateway_token", "payments", ["gateway_token"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_payments_gateway_token", table_name="payments")
    op.drop_column("payments", "gateway_token")
