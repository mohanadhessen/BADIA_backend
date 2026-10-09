"""Add payment gateway fields and subscriptions.

Revision ID: 8b3d1c4a6f20
Revises: edb75093d354
Create Date: 2026-10-09
"""
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "8b3d1c4a6f20"
down_revision: Union[str, Sequence[str], None] = "edb75093d354"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not context.is_offline_mode():
        connection = op.get_bind()
        orphaned_users = connection.execute(
            sa.text(
                "SELECT COUNT(*) FROM payments p "
                "LEFT JOIN users u ON u.id = p.user_id "
                "WHERE u.id IS NULL"
            )
        ).scalar_one()
        orphaned_plans = connection.execute(
            sa.text(
                "SELECT COUNT(*) FROM payments p "
                "LEFT JOIN plans pl ON pl.id = p.plan_id "
                "WHERE p.plan_id IS NOT NULL AND pl.id IS NULL"
            )
        ).scalar_one()
        if orphaned_users or orphaned_plans:
            raise RuntimeError(
                "Cannot add payment foreign keys: "
                f"{orphaned_users} payment(s) reference missing users and "
                f"{orphaned_plans} payment(s) reference missing plans."
            )

    op.add_column(
        "users",
        sa.Column("hash_id", sa.String(length=36), nullable=True),
    )
    op.execute(
        sa.text("UPDATE users SET hash_id = UUID() WHERE hash_id IS NULL")
    )
    op.alter_column(
        "users",
        "hash_id",
        existing_type=sa.String(length=36),
        nullable=False,
    )
    op.create_unique_constraint("uq_users_hash_id", "users", ["hash_id"])

    op.add_column(
        "payments",
        sa.Column("payment_hash_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("plan_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("currency", sa.String(length=3), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column(
            "source",
            sa.Enum("gateway", "admin", name="payment_source"),
            nullable=True,
        ),
    )
    op.add_column(
        "payments",
        sa.Column("hesabe_token", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("hesabe_reference_number", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("hesabe_transaction_id", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("hesabe_payment_id", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("hesabe_track_id", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("hesabe_payment_type", sa.String(length=50), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE payments p "
            "LEFT JOIN plans pl ON pl.id = p.plan_id "
            "SET p.payment_hash_id = UUID(), "
            "p.plan_name = COALESCE(pl.name, 'Legacy plan'), "
            "p.currency = 'KWD', "
            "p.source = 'gateway'"
        )
    )
    op.alter_column(
        "payments",
        "payment_hash_id",
        existing_type=sa.String(length=36),
        nullable=False,
    )
    op.alter_column(
        "payments",
        "plan_name",
        existing_type=sa.String(length=100),
        nullable=False,
    )
    op.alter_column(
        "payments",
        "currency",
        existing_type=sa.String(length=3),
        nullable=False,
    )
    op.alter_column(
        "payments",
        "source",
        existing_type=mysql.ENUM("gateway", "admin"),
        nullable=False,
    )
    op.alter_column(
        "payments",
        "amount",
        existing_type=mysql.DECIMAL(precision=10, scale=2),
        type_=mysql.DECIMAL(precision=11, scale=3),
        existing_nullable=False,
    )
    op.alter_column(
        "payments",
        "plan_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "payments",
        "billing_cycle",
        existing_type=mysql.ENUM("monthly", "yearly"),
        existing_nullable=False,
        nullable=True,
    )
    op.alter_column(
        "payments",
        "start_date",
        existing_type=mysql.TIMESTAMP(),
        existing_nullable=False,
        nullable=True,
    )
    op.alter_column(
        "payments",
        "end_date",
        existing_type=mysql.TIMESTAMP(),
        existing_nullable=False,
        nullable=True,
    )
    op.alter_column(
        "payments",
        "status",
        existing_type=mysql.ENUM("paid", "rejected", "canceled"),
        type_=mysql.ENUM("pending", "paid", "failed", "rejected", "canceled"),
        existing_nullable=False,
    )
    op.create_unique_constraint(
        "uq_payments_payment_hash_id", "payments", ["payment_hash_id"]
    )
    op.create_unique_constraint(
        "uq_payments_hesabe_token", "payments", ["hesabe_token"]
    )
    op.create_unique_constraint(
        "uq_payments_hesabe_reference_number",
        "payments",
        ["hesabe_reference_number"],
    )
    op.create_foreign_key(
        "fk_payments_user_id_users",
        "payments",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_payments_plan_id_plans",
        "payments",
        "plans",
        ["plan_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "expired", "canceled", name="subscription_status"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"], ["payments.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_id"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"], unique=True)
    op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])
    op.create_index("ix_subscriptions_created_at", "subscriptions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_subscriptions_created_at", table_name="subscriptions")
    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_plan_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_constraint("fk_payments_plan_id_plans", "payments", type_="foreignkey")
    op.drop_constraint("fk_payments_user_id_users", "payments", type_="foreignkey")
    op.drop_constraint(
        "uq_payments_hesabe_reference_number", "payments", type_="unique"
    )
    op.drop_constraint("uq_payments_hesabe_token", "payments", type_="unique")
    op.drop_constraint("uq_payments_payment_hash_id", "payments", type_="unique")
    op.alter_column(
        "payments",
        "status",
        existing_type=mysql.ENUM("pending", "paid", "failed", "rejected", "canceled"),
        type_=mysql.ENUM("paid", "rejected", "canceled"),
        existing_nullable=False,
    )
    op.alter_column(
        "payments",
        "plan_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "payments",
        "amount",
        existing_type=mysql.DECIMAL(precision=11, scale=3),
        type_=mysql.DECIMAL(precision=10, scale=2),
        existing_nullable=False,
    )

    op.drop_column("payments", "hesabe_payment_type")
    op.drop_column("payments", "hesabe_track_id")
    op.drop_column("payments", "hesabe_payment_id")
    op.drop_column("payments", "hesabe_transaction_id")
    op.drop_column("payments", "hesabe_reference_number")
    op.drop_column("payments", "hesabe_token")
    op.drop_column("payments", "source")
    op.drop_column("payments", "currency")
    op.drop_column("payments", "plan_name")
    op.drop_column("payments", "payment_hash_id")

    op.drop_constraint("uq_users_hash_id", "users", type_="unique")
    op.drop_column("users", "hash_id")
