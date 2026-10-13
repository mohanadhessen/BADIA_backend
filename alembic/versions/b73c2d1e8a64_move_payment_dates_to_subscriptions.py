"""Remove subscription dates from payments.

Revision ID: b73c2d1e8a64
Revises: a17e9c40b562
Create Date: 2026-10-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b73c2d1e8a64"
down_revision: Union[str, Sequence[str], None] = "a17e9c40b562"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Subscription dates are the canonical dates. Preserve any legacy payment
    # dates on the related subscription before removing the duplicate columns.
    op.execute(
        sa.text(
            """
            UPDATE subscriptions s
            JOIN payments p ON p.id = s.payment_id
            SET s.start_date = COALESCE(DATE(p.start_date), s.start_date),
                s.end_date = COALESCE(DATE(p.end_date), s.end_date)
            WHERE p.start_date IS NOT NULL OR p.end_date IS NOT NULL
            """
        )
    )
    op.drop_column("payments", "start_date")
    op.drop_column("payments", "end_date")


def downgrade() -> None:
    op.add_column(
        "payments", sa.Column("start_date", sa.TIMESTAMP(), nullable=True)
    )
    op.add_column(
        "payments", sa.Column("end_date", sa.TIMESTAMP(), nullable=True)
    )
    op.execute(
        sa.text(
            """
            UPDATE payments p
            JOIN subscriptions s ON s.payment_id = p.id
            SET p.start_date = s.start_date,
                p.end_date = s.end_date
            """
        )
    )
