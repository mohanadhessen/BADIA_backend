"""Move users from current plan fields to the subscription relationship.

Revision ID: a17e9c40b562
Revises: 4f3c2b9a1d70
Create Date: 2026-10-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a17e9c40b562"
down_revision: Union[str, Sequence[str], None] = "4f3c2b9a1d70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("current_subscription_id", sa.Integer(), nullable=True),
    )

    # Keep existing current-plan assignments when they have a corresponding
    # subscription. Users without a subscription have no equivalent record in
    # the new schema, so their new relationship remains NULL.
    op.execute(
        sa.text(
            """
            UPDATE users u
            JOIN (
                SELECT user_id, plan_id, MAX(id) AS subscription_id
                FROM subscriptions
                GROUP BY user_id, plan_id
            ) s ON s.user_id = u.id AND s.plan_id = u.current_plan_id
            SET u.current_subscription_id = s.subscription_id
            WHERE u.current_plan_id IS NOT NULL
            """
        )
    )

    op.create_unique_constraint(
        "uq_users_current_subscription_id",
        "users",
        ["current_subscription_id"],
    )
    op.create_foreign_key(
        "fk_users_current_subscription",
        "users",
        "subscriptions",
        ["current_subscription_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_constraint("fk_1", "users", type_="foreignkey")
    op.drop_index("ix_users_current_plan_id", table_name="users")
    op.drop_column("users", "subscription_end_date")
    op.drop_column("users", "current_plan_id")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("current_plan_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("subscription_end_date", sa.TIMESTAMP(), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE users u
            JOIN subscriptions s ON s.id = u.current_subscription_id
            SET u.current_plan_id = s.plan_id,
                u.subscription_end_date = s.end_date
            """
        )
    )

    op.drop_constraint(
        "fk_users_current_subscription", "users", type_="foreignkey"
    )
    op.drop_constraint(
        "uq_users_current_subscription_id", "users", type_="unique"
    )
    op.drop_column("users", "current_subscription_id")
    op.create_index("ix_users_current_plan_id", "users", ["current_plan_id"])
    op.create_foreign_key(
        "fk_1", "users", "plans", ["current_plan_id"], ["id"], ondelete="SET NULL"
    )
