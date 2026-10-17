"""Expand stored Hesabe checkout token length.

Revision ID: c2a6d9801f31
Revises: 8b3d1c4a6f20
Create Date: 2026-10-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2a6d9801f31"
down_revision: Union[str, Sequence[str], None] = "8b3d1c4a6f20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "payments",
        "hesabe_token",
        existing_type=sa.String(length=64),
        type_=sa.String(length=255),
        existing_nullable=True,
    )


def downgrade() -> None:
    connection = op.get_bind()
    long_tokens = connection.execute(
        sa.text("SELECT COUNT(*) FROM payments WHERE CHAR_LENGTH(hesabe_token) > 64")
    ).scalar_one()
    if long_tokens:
        raise RuntimeError(
            f"Cannot shrink hesabe_token to 64 characters: {long_tokens} longer value(s) exist."
        )
    op.alter_column(
        "payments",
        "hesabe_token",
        existing_type=sa.String(length=255),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
