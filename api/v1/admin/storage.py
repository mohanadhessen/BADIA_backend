from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from api.etag import compute_etag, check_etag, compute_db_etag
from r2_client import s3
from config import settings
from crud.email_metric import get_emails_metric
from models.UserFile import UserFile
from models.email_metric import EmailMetric

router = APIRouter(
    prefix="",
    tags=["Admin - Storage & Metrics"],
    dependencies=[Depends(require_admin)]
)

def get_bucket_storage_usage(s3, bucket_name):
    paginator = s3.get_paginator("list_objects_v2")

    total_bytes = 0
    total_files = 0

    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            total_bytes += obj["Size"]
            total_files += 1

    total_gb = total_bytes / (1024 ** 3)

    return {
        "total_bytes": total_bytes,
        "total_gb": round(total_gb, 4),
        "total_files": total_files,
    }

@router.get("/storage/usage")
@limiter.limit("10/minute")
def get_storage_usage(request: Request, response: Response, db: Session = Depends(get_db)):
    etag = compute_db_etag(db, UserFile)
    check_etag(request, etag)

    paginator = s3.get_paginator("list_objects_v2")

    total_bytes = 0
    total_files = 0

    for page in paginator.paginate(Bucket=settings.R2_BUCKET):
        for obj in page.get("Contents", []):
            total_bytes += obj["Size"]
            total_files += 1

    total_gb = total_bytes / (1024 ** 3)

    FREE_TIER_GB = 10  

    data = {
        "used_bytes": total_bytes,
        "used_kb": round(total_bytes / 1024, 2),
        "used_mb": round(total_bytes / (1024 ** 2), 4),
        "used_gb": round(total_bytes / (1024 ** 3), 6),
        "remaining_gb": round(max(FREE_TIER_GB - total_gb, 0), 6),
        "usage_percent": round((total_gb / FREE_TIER_GB) * 100, 6),
        "total_files": total_files,
    }
    
    response.headers["ETag"] = etag
    return data

@router.get("/emails/sent-this-month")
@limiter.limit("10/minute")
def get_email_count(request: Request, response: Response, db: Session = Depends(get_db)):
    etag = compute_db_etag(db, EmailMetric)
    check_etag(request, etag)
    
    data = get_emails_metric(db)
    response.headers["ETag"] = etag
    return data
