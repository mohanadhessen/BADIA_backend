from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from r2_client import s3
from config import settings
from crud.metrics import get_emails_metric
from models.user_file import UserFile
from models.email_metric import EmailMetric

router = APIRouter(
    prefix="",
    tags=["Admin - Storage & Metrics"],
    dependencies=[Depends(require_admin)]
)





@router.get("/emails/sent-this-month")
@limiter.limit("10/minute")
def get_email_count(request: Request, db: Session = Depends(get_db)):
    data = get_emails_metric(db)
    return data
