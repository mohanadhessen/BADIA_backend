"""Add the user hash ID column.

Revision ID: d4e8a1c7f203
Revises: b73c2d1e8a64
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e8a1c7f203"
down_revision: Union[str, Sequence[str], None] = "b73c2d1e8a64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("hashId", sa.String(length=36), nullable=True))
    op.execute(sa.text("UPDATE users SET `hashId` = UUID() WHERE `hashId` IS NULL"))
    op.alter_column(
        "users",
        "hashId",
        existing_type=sa.String(length=36),
        nullable=False,
    )
    op.create_unique_constraint("uq_users_hashId", "users", ["hashId"])


def downgrade() -> None:
    op.drop_constraint("uq_users_hashId", "users", type_="unique")
    op.drop_column("users", "hashId")
