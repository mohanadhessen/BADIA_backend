from fastapi import APIRouter, Depends, Response, Request
from starlette.status import HTTP_304_NOT_MODIFIED
from sqlalchemy.orm import Session
from database.session import get_db 
from crud.plan import  get_all_plans , get_plans_cache_metadata
from schemas.plan import PlanResponse
import hashlib
from api.rate_limiter import limiter


router = APIRouter(tags=["Plans"])


from api.etag import compute_etag, check_etag


@router.get("/", response_model=list[PlanResponse])
@limiter.limit("60/minute")
def list_plans(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    plans = get_all_plans(db)
    
    etag = compute_etag(plans)
    check_etag(request, etag)
    
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "no-cache"

    return plans