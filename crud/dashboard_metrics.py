from sqlalchemy.orm import Session
from sqlalchemy import select, func, case , update , and_

from models.dashboard_metrics import DashboardMetrics
from models.user import User
from models.payment import Payment
from models.review import Review
from models.request import Request
from models.plan import Plan
from datetime import datetime

import time


def get_dashboard_metrics(db: Session):
    start_total = time.perf_counter()

    # 1) cached metrics query
    t0 = time.perf_counter()
    metrics = db.query(DashboardMetrics).first()
    if not metrics:
        metrics = DashboardMetrics(id=1)
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
    t1 = time.perf_counter()

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 2) live aggregation query
    t2 = time.perf_counter()
    live_row = db.execute(
        select(
            func.sum(case((Payment.start_date >= month_start, 1), else_=0)).label("payments_this_month"),
            func.sum(
                case(
                    (and_(Payment.status == "paid", Payment.start_date >= month_start), Payment.amount),
                    else_=0,
                )
            ).label("revenue_this_month"),
        )
    ).one()
    t3 = time.perf_counter()

    total_ms = (time.perf_counter() - start_total) * 1000

    return {
        "total_users": metrics.total_users,
        "active_users": metrics.active_users,
        "inactive_users": metrics.inactive_users,
        "verified_users": metrics.verified_users,
        "unverified_users": metrics.unverified_users,
        "plans_distribution": metrics.plans_distribution,
        "total_payments": metrics.total_payments,
        "paid_payments": metrics.paid_payments,
        "rejected_payments": metrics.rejected_payments,
        "canceled_payments": metrics.canceled_payments,
        "monthly_payments": metrics.monthly_payments,
        "yearly_payments": metrics.yearly_payments,
        "total_revenue": metrics.total_revenue,
        "total_reviews": metrics.total_reviews,
        "published_reviews": metrics.published_reviews,
        "pending_reviews": metrics.pending_reviews,
        "total_requests": metrics.total_requests,
        "pending_requests": metrics.pending_requests,
        "approved_requests": metrics.approved_requests,
        "rejected_requests": metrics.rejected_requests,
        "updated_at": metrics.updated_at,

        "payments_this_month": int(live_row.payments_this_month or 0),
        "revenue_this_month": live_row.revenue_this_month or 0,

        # latency metrics (ms)
        "latency_ms": {
            "metrics_query": (t1 - t0) * 1000,
            "live_query": (t3 - t2) * 1000,
            "total": total_ms,
        },
    }






def refresh_user_metrics(db: Session):
    row = db.execute(
        select(
            func.count(User.id).label("total"),
            func.sum(case((User.is_active == True, 1), else_=0)).label("active"),
            func.sum(case((User.is_active == False, 1), else_=0)).label("inactive"),
            func.sum(case((User.is_email_verified == True, 1), else_=0)).label("verified"),
            func.sum(case((User.is_email_verified == False, 1), else_=0)).label("unverified"),
        )
    ).one()

    plan_rows = db.execute(
        select(
            User.current_plan_id.label("plan_id"),
            func.count(User.id).label("count"),
        )
        .group_by(User.current_plan_id)
    ).all()

    plan_names = {
        p.id: p.name
        for p in db.execute(select(Plan.id, Plan.name)).all()
    }

    plans_distribution = {
        (plan_names.get(plan_id, "no_plan") if plan_id is not None else "no_plan"): count
        for plan_id, count in plan_rows
    }

    db.execute(
        update(DashboardMetrics)
        .where(DashboardMetrics.id == 1)
        .values(
            total_users=row.total,
            active_users=row.active,
            inactive_users=row.inactive,
            verified_users=row.verified,
            unverified_users=row.unverified,
            plans_distribution=plans_distribution,
        )
    )

    db.commit()





def refresh_review_metrics(db: Session):
    row = db.execute(
        select(
            func.count(Review.id).label("total_reviews"),
            func.sum(case((Review.is_published == True, 1), else_=0)).label("published_reviews"),
            func.sum(case((Review.is_published == False, 1), else_=0)).label("pending_reviews"),
        )
    ).one()

    db.execute(
        update(DashboardMetrics)
        .where(DashboardMetrics.id == 1)
        .values(
            total_reviews=row.total_reviews,
            published_reviews=row.published_reviews,
            pending_reviews=row.pending_reviews,
        )
    )
    db.commit()



def refresh_requests_metrics(db: Session):
    row = db.execute(
        select(
            func.count(Request.id).label("total_requests"),
            func.sum(case((Request.status == "pending", 1), else_=0)).label("pending_requests"),
            func.sum(case((Request.status == "approved", 1), else_=0)).label("approved_requests"),
            func.sum(case((Request.status == "rejected", 1), else_=0)).label("rejected_requests"),
        )
    ).one()

    db.execute(
        update(DashboardMetrics)
        .where(DashboardMetrics.id == 1)
        .values(
            total_requests=row.total_requests,
            pending_requests=row.pending_requests,
            approved_requests=row.approved_requests,
            rejected_requests=row.rejected_requests,
        )
    )
    db.commit()
    



def refresh_payment_metrics(db: Session):
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    row = db.execute(
        select(
            func.count(Payment.id).label("total_payments"),
            func.sum(case((Payment.status == "paid", 1), else_=0)).label("paid_payments"),
            func.sum(case((Payment.status == "rejected", 1), else_=0)).label("rejected_payments"),
            func.sum(case((Payment.status == "canceled", 1), else_=0)).label("canceled_payments"),
            func.sum(case((Payment.billing_cycle == "monthly", 1), else_=0)).label("monthly_payments"),
            func.sum(case((Payment.billing_cycle == "yearly", 1), else_=0)).label("yearly_payments"),
            func.sum(
                case((Payment.start_date >= month_start, 1), else_=0)
            ).label("payments_this_month"),
            func.sum(
                case((Payment.status == "paid", Payment.amount), else_=0)
            ).label("total_revenue"),
            func.sum(
                case(
                    (and_(Payment.status == "paid", Payment.start_date >= month_start), Payment.amount),
                    else_=0,
                )
            ).label("revenue_this_month"),
        )
    ).one()

    db.execute(
        update(DashboardMetrics)
        .where(DashboardMetrics.id == 1)
        .values(
            total_payments=row.total_payments,
            paid_payments=row.paid_payments,
            rejected_payments=row.rejected_payments,
            canceled_payments=row.canceled_payments,
            monthly_payments=row.monthly_payments,
            yearly_payments=row.yearly_payments,
            total_revenue=row.total_revenue or 0,
        )
    )
    db.commit()







def get_this_month_payment_stats(db: Session):
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    row = db.execute(
        select(
            func.sum(case((Payment.start_date >= month_start, 1), else_=0)).label("payments_this_month"),
            func.sum(
                case(
                    (and_(Payment.status == "paid", Payment.start_date >= month_start), Payment.amount),
                    else_=0,
                )
            ).label("revenue_this_month"),
        )
    ).one()

    return {
        "payments_this_month": row.payments_this_month or 0,
        "revenue_this_month": row.revenue_this_month or 0,
    }