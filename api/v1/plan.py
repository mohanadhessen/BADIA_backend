from fastapi import APIRouter, Depends, Response, Request
from starlette.status import HTTP_304_NOT_MODIFIED
from sqlalchemy.orm import Session
from database.session import get_db 
from crud.plan import  get_all_plans , get_plans_cache_metadata
from schemas.plan import PlanResponse
import hashlib
from api.rate_limiter import limiter
from models.plan import Plan
from api.etag import compute_db_etag, check_etag


router = APIRouter(tags=["Plans"])


@router.get("/", response_model=list[PlanResponse])
@limiter.limit("60/minute")
def list_plans(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    etag = compute_db_etag(db, Plan)
    check_etag(request, etag)
    
    plans = get_all_plans(db)
    
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "no-cache"

    return plans