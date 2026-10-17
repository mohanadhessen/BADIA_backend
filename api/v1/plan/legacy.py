from fastapi import APIRouter, Depends, Request, Response
from starlette.status import HTTP_304_NOT_MODIFIED
from sqlalchemy.orm import Session
from database.session import get_db
from crud.plan import get_all_plans
from schemas.plan import PlanResponse
from api.rate_limiter import limiter
from cache.plans import bump_plans_version, get_plans_version
from cache.etags import make_etag, check_etag


router = APIRouter(tags=["Plans"])


@router.get("/", response_model=list[PlanResponse])
@limiter.limit("60/minute")
def list_plans(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    version = get_plans_version()
    if version == 0:
        bump_plans_version()
        version = 1

    etag = make_etag(version)
    if check_etag(request, response, etag):
        return []

    plans = get_all_plans(db)
    return plans