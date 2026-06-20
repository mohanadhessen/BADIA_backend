from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
import sentry_sdk
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from api.etag import check_etag, compute_global_db_etag
from r2_client import s3
from config import settings

from models.user import User
from models.plan import Plan
from models.review import Review
from models.request import Request as DBRequest
from models.payment import Payment
from models.email_metric import EmailMetric
from models.UserFile import UserFile

from crud.user import admin_get_all_users, get_users_plans_distribution
from crud.review import admin_get_all_review
from crud.request import admin_get_all_requests
from crud.payment import admin_get_all_payments
from crud.plan import get_all_plans
from crud.email_metric import get_emails_metric

router = APIRouter(
    prefix="",
    tags=["Admin - Dashboard"],
    dependencies=[Depends(require_admin)]
)

def get_storage_usage_safe():
    try:
        paginator = s3.get_paginator("list_objects_v2")
        total_bytes = 0
        total_files = 0
        for page in paginator.paginate(Bucket=settings.R2_BUCKET):
            for obj in page.get("Contents", []):
                total_bytes += obj["Size"]
                total_files += 1
        total_gb = total_bytes / (1024 ** 3)
        FREE_TIER_GB = 10
        return {
            "used_bytes": total_bytes,
            "used_kb": round(total_bytes / 1024, 2),
            "used_mb": round(total_bytes / (1024 ** 2), 4),
            "used_gb": round(total_bytes / (1024 ** 3), 6),
            "remaining_gb": round(max(FREE_TIER_GB - total_gb, 0), 6),
            "usage_percent": round((total_gb / FREE_TIER_GB) * 100, 6),
            "total_files": total_files,
        }
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return {
            "error": f"Failed to retrieve storage usage: {str(e)}",
            "used_bytes": 0,
            "used_kb": 0,
            "used_mb": 0,
            "used_gb": 0,
            "remaining_gb": 10,
            "usage_percent": 0,
            "total_files": 0,
        }

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
    # 1. Fast, lightweight ETag pre-check (checks only total counts and max updated_at for all models)
    etag = compute_global_db_etag(db, [User, Plan, Review, DBRequest, Payment, EmailMetric, UserFile])
    check_etag(request, etag)

    # 2. Fetch full data only if ETag did not match (Client doesn't have the current version)
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
        limit=requests_limit
    )
    payments_data = admin_get_all_payments(
        db=db,
        page=payments_page,
        limit=payments_limit,
        status=payments_status
    )
    storage_data = get_storage_usage_safe()
    emails_data = get_emails_metric(db=db)
    plans_list = get_all_plans(db=db)

    dashboard_data = {
        "users": users_data,
        "plans_distribution": plans_distribution,
        "reviews": reviews_data,
        "requests": requests_data,
        "payments": payments_data,
        "storage": storage_data,
        "emails": emails_data,
        "plans": plans_list,
    }

    response.headers["ETag"] = etag
    return dashboard_data
