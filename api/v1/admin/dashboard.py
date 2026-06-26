from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from crud.user import admin_get_all_users, get_users_plans_distribution
from crud.review import admin_get_all_review
from crud.request import admin_get_all_requests
from crud.payment import admin_get_all_payments
from crud.plan import get_all_plans
from crud.metrics import get_emails_metric, get_files_metric
from crud.dashboard_metrics import get_dashboard_metrics
from cache.dashboard import get_dashboard_version
from cache.etags import check_etag, make_etag

router = APIRouter(
    prefix="",
    tags=["Admin - Dashboard"],
    dependencies=[Depends(require_admin)]
)


@router.get("/dashboard")
@limiter.limit("30/minute")
def get_dashboard_data(
    request: Request,
    response: Response,
    users_page: int = 1,
    users_limit: int = 5,
    users_only_active: bool = False,
    reviews_page: int = 1,
    reviews_limit: int = 5,
    requests_page: int = 1,
    requests_limit: int = 5,
    payments_page: int = 1,
    payments_limit: int = 5,
    payments_status: str | None = None,
    db: Session = Depends(get_db)
):
    version = get_dashboard_version()
    etag_str = f"{version}:{users_page}:{users_limit}:{users_only_active}:{reviews_page}:{reviews_limit}:{requests_page}:{requests_limit}:{payments_page}:{payments_limit}:{payments_status}"
    etag = make_etag(etag_str)
    if check_etag(request, response, etag):
        return {}

    metrics_row = get_dashboard_metrics(db)

    metrics = {}
    if metrics_row:
        metrics = {
            "users": {
                "total_users": metrics_row.get("total_users"),
            },
            "payments": {
                "paid_payments": metrics_row.get("paid_payments"),
                "total_revenue": float(metrics_row.get("total_revenue", 0)),
            },
            "reviews": {
                "total_reviews": metrics_row.get("total_reviews"),
                "published_reviews": metrics_row.get("published_reviews"),
                "pending_reviews": metrics_row.get("pending_reviews"),
            },
            "requests": {
                "total_requests": metrics_row.get("total_requests"),
                "pending_requests": metrics_row.get("pending_requests"),
                "approved_requests": metrics_row.get("approved_requests"),
                "rejected_requests": metrics_row.get("rejected_requests"),
            },
            "updated_at": metrics_row.get("updated_at"),
        }

    users_data = admin_get_all_users(
        db=db,
        page=users_page,
        limit=users_limit,
        only_active=users_only_active
    )

    plans_distribution = get_users_plans_distribution(db=db)

    reviews_data = admin_get_all_review(
        db=db,
        page=reviews_page,
        limit=reviews_limit,
        pending_only=True
    )

    requests_data = admin_get_all_requests(
        db=db,
        page=requests_page,
        limit=requests_limit,
        status="pending"
    )

    payments_data = admin_get_all_payments(
        db=db,
        page=payments_page,
        limit=payments_limit,
        status=payments_status
    )

    storage_data = get_files_metric(db)

    emails_data = get_emails_metric(db)

    plans_list = get_all_plans(db)

    dashboard_data = {
        "metrics": metrics,
        "users": users_data,
        "plans_distribution": plans_distribution,
        "reviews": reviews_data,
        "requests": requests_data,
        "payments": payments_data,
        "storage": storage_data,
        "emails": emails_data,
        "plans": plans_list,
    }

    return dashboard_data