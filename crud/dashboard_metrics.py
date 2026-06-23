from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import Optional

from models.dashboard_metrics import DashboardMetrics
from models.user import User
from models.payment import Payment
from models.review import Review
from models.request import Request


SINGLETON_ID = 1


# ──────────────────────────────────────────────
#  Core helpers
# ──────────────────────────────────────────────

def get_dashboard_metrics(db: Session) -> Optional[DashboardMetrics]:
    """Return the single dashboard-metrics row (or None if it hasn't been seeded)."""
    return db.query(DashboardMetrics).filter(DashboardMetrics.id == SINGLETON_ID).first()


def upsert_dashboard_metrics(db: Session, **kwargs) -> DashboardMetrics:
    """
    Insert the singleton row if it doesn't exist, otherwise update only the
    supplied keyword arguments.  Accepts any column name defined on the model.
    """
    row = get_dashboard_metrics(db)
    if row is None:
        row = DashboardMetrics(id=SINGLETON_ID, **kwargs)
        db.add(row)
    else:
        for key, value in kwargs.items():
            if hasattr(row, key):
                setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


# ──────────────────────────────────────────────
#  Individual field updaters
# ──────────────────────────────────────────────

# -- Users --
def update_total_users(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, total_users=value)

def update_active_users(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, active_users=value)

def update_inactive_users(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, inactive_users=value)

def update_verified_users(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, verified_users=value)

def update_unverified_users(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, unverified_users=value)

# -- Payments --
def update_total_payments(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, total_payments=value)

def update_paid_payments(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, paid_payments=value)

def update_rejected_payments(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, rejected_payments=value)

def update_canceled_payments(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, canceled_payments=value)

def update_monthly_payments(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, monthly_payments=value)

def update_yearly_payments(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, yearly_payments=value)

def update_total_revenue(db: Session, value: Decimal) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, total_revenue=value)

# -- Reviews --
def update_total_reviews(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, total_reviews=value)

def update_published_reviews(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, published_reviews=value)

def update_pending_reviews(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, pending_reviews=value)

# -- Requests --
def update_total_requests(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, total_requests=value)

def update_pending_requests(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, pending_requests=value)

def update_approved_requests(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, approved_requests=value)

def update_rejected_requests(db: Session, value: int) -> DashboardMetrics:
    return upsert_dashboard_metrics(db, rejected_requests=value)


# ──────────────────────────────────────────────
#  Bulk updaters (set all fields in a group)
# ──────────────────────────────────────────────

def update_user_metrics(
    db: Session,
    total_users: int,
    active_users: int,
    inactive_users: int,
    verified_users: int,
    unverified_users: int,
) -> DashboardMetrics:
    return upsert_dashboard_metrics(
        db,
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        verified_users=verified_users,
        unverified_users=unverified_users,
    )


def update_payment_metrics(
    db: Session,
    total_payments: int,
    paid_payments: int,
    rejected_payments: int,
    canceled_payments: int,
    monthly_payments: int,
    yearly_payments: int,
    total_revenue: Decimal,
) -> DashboardMetrics:
    return upsert_dashboard_metrics(
        db,
        total_payments=total_payments,
        paid_payments=paid_payments,
        rejected_payments=rejected_payments,
        canceled_payments=canceled_payments,
        monthly_payments=monthly_payments,
        yearly_payments=yearly_payments,
        total_revenue=total_revenue,
    )


def update_review_metrics(
    db: Session,
    total_reviews: int,
    published_reviews: int,
    pending_reviews: int,
) -> DashboardMetrics:
    return upsert_dashboard_metrics(
        db,
        total_reviews=total_reviews,
        published_reviews=published_reviews,
        pending_reviews=pending_reviews,
    )


def update_request_metrics(
    db: Session,
    total_requests: int,
    pending_requests: int,
    approved_requests: int,
    rejected_requests: int,
) -> DashboardMetrics:
    return upsert_dashboard_metrics(
        db,
        total_requests=total_requests,
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        rejected_requests=rejected_requests,
    )


def update_all_metrics(
    db: Session,
    total_users: int, active_users: int, inactive_users: int,
    verified_users: int, unverified_users: int,
    total_payments: int, paid_payments: int, rejected_payments: int,
    canceled_payments: int, monthly_payments: int, yearly_payments: int,
    total_revenue: Decimal,
    total_reviews: int, published_reviews: int, pending_reviews: int,
    total_requests: int, pending_requests: int,
    approved_requests: int, rejected_requests: int,
) -> DashboardMetrics:
    return upsert_dashboard_metrics(
        db,
        total_users=total_users, active_users=active_users,
        inactive_users=inactive_users, verified_users=verified_users,
        unverified_users=unverified_users,
        total_payments=total_payments, paid_payments=paid_payments,
        rejected_payments=rejected_payments, canceled_payments=canceled_payments,
        monthly_payments=monthly_payments, yearly_payments=yearly_payments,
        total_revenue=total_revenue,
        total_reviews=total_reviews, published_reviews=published_reviews,
        pending_reviews=pending_reviews,
        total_requests=total_requests, pending_requests=pending_requests,
        approved_requests=approved_requests, rejected_requests=rejected_requests,
    )


# ══════════════════════════════════════════════
#  REFRESH helpers — re-count from live tables
#  Call these after any mutation that affects
#  the corresponding entity.
# ══════════════════════════════════════════════

def refresh_user_metrics(db: Session) -> DashboardMetrics:
    """Re-count every user metric from the users table and persist."""
    base = db.query(func.count(User.id)).filter(User.role == "user")

    total    = base.scalar() or 0
    active   = base.filter(User.is_active == True).scalar() or 0
    inactive = base.filter(User.is_active == False).scalar() or 0
    verified = base.filter(User.is_email_verified == True).scalar() or 0
    unverified = base.filter(User.is_email_verified == False).scalar() or 0

    return upsert_dashboard_metrics(
        db,
        total_users=total,
        active_users=active,
        inactive_users=inactive,
        verified_users=verified,
        unverified_users=unverified,
    )


def refresh_payment_metrics(db: Session) -> DashboardMetrics:
    """Re-count every payment metric from the payments table and persist."""
    total     = db.query(func.count(Payment.id)).scalar() or 0
    paid      = db.query(func.count(Payment.id)).filter(Payment.status == "paid").scalar() or 0
    rejected  = db.query(func.count(Payment.id)).filter(Payment.status == "rejected").scalar() or 0
    canceled  = db.query(func.count(Payment.id)).filter(Payment.status == "canceled").scalar() or 0
    monthly   = db.query(func.count(Payment.id)).filter(Payment.billing_cycle == "monthly").scalar() or 0
    yearly    = db.query(func.count(Payment.id)).filter(Payment.billing_cycle == "yearly").scalar() or 0
    revenue   = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status.in_(["paid", "canceled"]))
        .scalar()
    )

    return upsert_dashboard_metrics(
        db,
        total_payments=total,
        paid_payments=paid,
        rejected_payments=rejected,
        canceled_payments=canceled,
        monthly_payments=monthly,
        yearly_payments=yearly,
        total_revenue=revenue,
    )


def refresh_review_metrics(db: Session) -> DashboardMetrics:
    """Re-count every review metric from the reviews table and persist."""
    total     = db.query(func.count(Review.id)).scalar() or 0
    published = db.query(func.count(Review.id)).filter(Review.is_published == True).scalar() or 0
    pending   = db.query(func.count(Review.id)).filter(Review.is_published == False).scalar() or 0

    return upsert_dashboard_metrics(
        db,
        total_reviews=total,
        published_reviews=published,
        pending_reviews=pending,
    )


def refresh_request_metrics(db: Session) -> DashboardMetrics:
    """Re-count every request metric from the requests table and persist."""
    total    = db.query(func.count(Request.id)).scalar() or 0
    pending  = db.query(func.count(Request.id)).filter(Request.status == "pending").scalar() or 0
    approved = db.query(func.count(Request.id)).filter(Request.status == "approved").scalar() or 0
    rejected = db.query(func.count(Request.id)).filter(Request.status == "rejected").scalar() or 0

    return upsert_dashboard_metrics(
        db,
        total_requests=total,
        pending_requests=pending,
        approved_requests=approved,
        rejected_requests=rejected,
    )


def refresh_all_metrics(db: Session) -> DashboardMetrics:
    """Full refresh — re-counts every metric from every source table."""
    # Users
    user_base = db.query(func.count(User.id)).filter(User.role == "user")
    total_users    = user_base.scalar() or 0
    active_users   = db.query(func.count(User.id)).filter(User.role == "user", User.is_active == True).scalar() or 0
    inactive_users = db.query(func.count(User.id)).filter(User.role == "user", User.is_active == False).scalar() or 0
    verified_users = db.query(func.count(User.id)).filter(User.role == "user", User.is_email_verified == True).scalar() or 0
    unverified_users = db.query(func.count(User.id)).filter(User.role == "user", User.is_email_verified == False).scalar() or 0

    # Payments
    total_payments = db.query(func.count(Payment.id)).scalar() or 0
    paid_payments  = db.query(func.count(Payment.id)).filter(Payment.status == "paid").scalar() or 0
    rejected_payments = db.query(func.count(Payment.id)).filter(Payment.status == "rejected").scalar() or 0
    canceled_payments = db.query(func.count(Payment.id)).filter(Payment.status == "canceled").scalar() or 0
    monthly_payments  = db.query(func.count(Payment.id)).filter(Payment.billing_cycle == "monthly").scalar() or 0
    yearly_payments   = db.query(func.count(Payment.id)).filter(Payment.billing_cycle == "yearly").scalar() or 0
    total_revenue = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status.in_(["paid", "canceled"]))
        .scalar()
    )

    # Reviews
    total_reviews     = db.query(func.count(Review.id)).scalar() or 0
    published_reviews = db.query(func.count(Review.id)).filter(Review.is_published == True).scalar() or 0
    pending_reviews   = db.query(func.count(Review.id)).filter(Review.is_published == False).scalar() or 0

    # Requests
    total_requests    = db.query(func.count(Request.id)).scalar() or 0
    pending_requests  = db.query(func.count(Request.id)).filter(Request.status == "pending").scalar() or 0
    approved_requests = db.query(func.count(Request.id)).filter(Request.status == "approved").scalar() or 0
    rejected_requests = db.query(func.count(Request.id)).filter(Request.status == "rejected").scalar() or 0

    return upsert_dashboard_metrics(
        db,
        total_users=total_users, active_users=active_users,
        inactive_users=inactive_users, verified_users=verified_users,
        unverified_users=unverified_users,
        total_payments=total_payments, paid_payments=paid_payments,
        rejected_payments=rejected_payments, canceled_payments=canceled_payments,
        monthly_payments=monthly_payments, yearly_payments=yearly_payments,
        total_revenue=total_revenue,
        total_reviews=total_reviews, published_reviews=published_reviews,
        pending_reviews=pending_reviews,
        total_requests=total_requests, pending_requests=pending_requests,
        approved_requests=approved_requests, rejected_requests=rejected_requests,
    )
