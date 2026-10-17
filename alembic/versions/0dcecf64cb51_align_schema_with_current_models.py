"""align schema with current models

Revision ID: 0dcecf64cb51
Revises: c2a6d9801f31
Create Date: 2026-10-10 04:42:20.690945

"""
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = '0dcecf64cb51'
down_revision: Union[str, Sequence[str], None] = 'c2a6d9801f31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    if not context.is_offline_mode():
        invalid = (
            connection.execute(
                sa.text(
                    """
                    SELECT
                        COALESCE(SUM(billing_cycle IS NULL), 0) AS null_billing_cycle,
                        COALESCE(SUM(source IS NULL OR source NOT IN ('gateway', 'admin')), 0) AS invalid_source,
                        COALESCE(SUM(status NOT IN ('pending', 'paid', 'failed', 'rejected', 'canceled')), 0) AS invalid_status,
                        COALESCE(SUM(amount != ROUND(amount, 2) OR ABS(amount) >= 100000000), 0) AS invalid_amount,
                        COALESCE(SUM(payment_hash_id IS NULL), 0) AS null_payment_hash
                    FROM payments
                    """
                )
            )
            .mappings()
            .one()
        )
        invalid_values = {
            name: int(value or 0) for name, value in invalid.items()
        }
        invalid_values = {
            name: count for name, count in invalid_values.items() if count
        }
        if invalid_values:
            raise RuntimeError(
                "Cannot align payments with the current models without losing or "
                f"changing data: {invalid_values}"
            )

    op.execute(
        sa.text("UPDATE payments SET status = 'failed' WHERE status = 'rejected'")
    )
    op.alter_column(
        "payments",
        "status",
        existing_type=mysql.ENUM(
            "pending", "paid", "failed", "rejected", "canceled"
        ),
        type_=mysql.ENUM("pending", "paid", "failed", "canceled"),
        existing_nullable=False,
    )

    op.alter_column(
        "payments",
        "source",
        existing_type=mysql.ENUM("gateway", "admin"),
        type_=mysql.ENUM("gateway", "admin", "manual", "paymentgateway"),
        existing_nullable=False,
    )
    op.execute(
        sa.text(
            """
            UPDATE payments
            SET source = CASE source
                WHEN 'gateway' THEN 'paymentgateway'
                WHEN 'admin' THEN 'manual'
                ELSE source
            END
            """
        )
    )
    op.alter_column(
        "payments",
        "source",
        existing_type=mysql.ENUM(
            "gateway", "admin", "manual", "paymentgateway"
        ),
        type_=mysql.ENUM("manual", "paymentgateway", name="payment_source"),
        existing_nullable=False,
    )

    op.alter_column(
        "payments",
        "amount",
        existing_type=mysql.DECIMAL(precision=11, scale=3),
        type_=sa.Numeric(precision=10, scale=2),
        existing_nullable=False,
    )
    op.alter_column(
        "payments",
        "billing_cycle",
        existing_type=mysql.ENUM("monthly", "yearly"),
        nullable=False,
        existing_nullable=True,
    )

    op.drop_index("uq_payments_payment_hash_id", table_name="payments")
    op.alter_column(
        "payments",
        "payment_hash_id",
        new_column_name="payment_hash",
        existing_type=sa.String(length=36),
        type_=sa.String(length=64),
        existing_nullable=False,
    )
    op.create_unique_constraint(
        "uq_payments_payment_hash", "payments", ["payment_hash"]
    )
    op.create_index("ix_payments_source", "payments", ["source"], unique=False)

    op.drop_index(
        "uq_payments_hesabe_reference_number", table_name="payments"
    )
    op.drop_index("uq_payments_hesabe_token", table_name="payments")
    op.drop_column("payments", "hesabe_payment_type")
    op.drop_column("payments", "hesabe_reference_number")
    op.drop_column("payments", "hesabe_transaction_id")
    op.drop_column("payments", "currency")
    op.drop_column("payments", "plan_name")
    op.drop_column("payments", "hesabe_token")
    op.drop_column("payments", "hesabe_payment_id")
    op.drop_column("payments", "hesabe_track_id")

    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.create_index(
        "ix_subscriptions_user_id", "subscriptions", ["user_id"], unique=False
    )

    op.drop_index("uq_users_hash_id", table_name="users")
    op.drop_column("users", "hash_id")


def downgrade() -> None:
    """Restore the previous schema; discarded gateway values cannot be recovered."""
    if not context.is_offline_mode():
        connection = op.get_bind()
        long_hashes = connection.execute(
            sa.text(
                "SELECT COUNT(*) FROM payments WHERE CHAR_LENGTH(payment_hash) > 36"
            )
        ).scalar_one()
        duplicate_subscriptions = connection.execute(
            sa.text(
                """
                SELECT COUNT(*) FROM (
                    SELECT user_id
                    FROM subscriptions
                    GROUP BY user_id
                    HAVING COUNT(*) > 1
                ) AS duplicate_users
                """
            )
        ).scalar_one()
        if long_hashes or duplicate_subscriptions:
            raise RuntimeError(
                "Cannot restore the previous schema: "
                f"{long_hashes} payment hash(es) exceed 36 characters and "
                f"{duplicate_subscriptions} user(s) have multiple subscriptions."
            )

    op.add_column(
        "users", sa.Column("hash_id", sa.String(length=36), nullable=True)
    )
    op.execute(sa.text("UPDATE users SET hash_id = UUID() WHERE hash_id IS NULL"))
    op.alter_column(
        "users", "hash_id", existing_type=sa.String(length=36), nullable=False
    )
    op.create_index("uq_users_hash_id", "users", ["hash_id"], unique=True)

    op.add_column(
        "payments", sa.Column("hesabe_payment_type", sa.String(length=50))
    )
    op.add_column(
        "payments",
        sa.Column("hesabe_reference_number", sa.String(length=100)),
    )
    op.add_column(
        "payments",
        sa.Column("hesabe_transaction_id", sa.String(length=100)),
    )
    op.add_column(
        "payments",
        sa.Column("currency", sa.String(length=3), nullable=True),
    )
    op.execute(sa.text("UPDATE payments SET currency = 'KWD' WHERE currency IS NULL"))
    op.alter_column(
        "payments", "currency", existing_type=sa.String(length=3), nullable=False
    )
    op.add_column(
        "payments",
        sa.Column("plan_name", sa.String(length=100), nullable=True),
    )
    op.execute(
        sa.text("UPDATE payments SET plan_name = 'Legacy plan' WHERE plan_name IS NULL")
    )
    op.alter_column(
        "payments", "plan_name", existing_type=sa.String(length=100), nullable=False
    )
    op.add_column(
        "payments", sa.Column("hesabe_token", sa.String(length=255))
    )
    op.add_column(
        "payments", sa.Column("hesabe_payment_id", sa.String(length=100))
    )
    op.add_column(
        "payments", sa.Column("hesabe_track_id", sa.String(length=100))
    )

    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.create_index(
        "ix_subscriptions_user_id", "subscriptions", ["user_id"], unique=True
    )

    op.drop_constraint("uq_payments_payment_hash", "payments", type_="unique")
    op.alter_column(
        "payments",
        "payment_hash",
        new_column_name="payment_hash_id",
        existing_type=sa.String(length=64),
        type_=sa.String(length=36),
        existing_nullable=False,
    )
    op.create_index(
        "uq_payments_payment_hash_id",
        "payments",
        ["payment_hash_id"],
        unique=True,
    )

    op.create_index(
        "uq_payments_hesabe_reference_number",
        "payments",
        ["hesabe_reference_number"],
        unique=True,
    )
    op.create_index(
        "uq_payments_hesabe_token", "payments", ["hesabe_token"], unique=True
    )
    op.drop_index("ix_payments_source", table_name="payments")

    op.alter_column(
        "payments",
        "source",
        existing_type=mysql.ENUM("manual", "paymentgateway"),
        type_=mysql.ENUM("gateway", "admin", "manual", "paymentgateway"),
        existing_nullable=False,
    )
    op.execute(
        sa.text(
            """
            UPDATE payments
            SET source = CASE source
                WHEN 'paymentgateway' THEN 'gateway'
                WHEN 'manual' THEN 'admin'
                ELSE source
            END
            """
        )
    )
    op.alter_column(
        "payments",
        "source",
        existing_type=mysql.ENUM(
            "gateway", "admin", "manual", "paymentgateway"
        ),
        type_=mysql.ENUM("gateway", "admin"),
        existing_nullable=False,
    )
    op.alter_column(
        "payments",
        "status",
        existing_type=mysql.ENUM("pending", "paid", "failed", "canceled"),
        type_=mysql.ENUM("pending", "paid", "failed", "rejected", "canceled"),
        existing_nullable=False,
    )
    op.alter_column(
        "payments",
        "billing_cycle",
        existing_type=mysql.ENUM("monthly", "yearly"),
        nullable=True,
        existing_nullable=False,
    )
    op.alter_column(
        "payments",
        "amount",
        existing_type=sa.Numeric(precision=10, scale=2),
        type_=mysql.DECIMAL(precision=11, scale=3),
        existing_nullable=False,
    )
