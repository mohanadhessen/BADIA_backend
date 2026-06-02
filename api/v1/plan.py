from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session
from database.session import get_db 
from crud.plan import  get_all_plans , get_plans_cache_metadata
from schemas.plan import PlanResponse
import hashlib
import json


router = APIRouter()


def make_etag(plans):
    raw = json.dumps([p.id for p in plans], sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


@router.get("/", response_model=list[PlanResponse])
def list_plans(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    plans = get_all_plans(db)

    if not plans:
        response.headers["Cache-Control"] = "public, max-age=60"
        return []

    # ---- ETag cache (main fix) ----
    etag = make_etag(plans)
    client_etag = request.headers.get("if-none-match")

    if client_etag == etag:
        return Response(status_code=304)

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=60"

    # ---- optional Last-Modified (backup compatibility) ----
    meta = get_plans_cache_metadata(db)
    last_updated = meta.get("last_updated")

    if last_updated:
        response.headers["Last-Modified"] = last_updated.strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

    return plans