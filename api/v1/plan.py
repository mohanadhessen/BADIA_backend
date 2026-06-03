from fastapi import APIRouter, Depends, Response, Request
from starlette.status import HTTP_304_NOT_MODIFIED
from sqlalchemy.orm import Session
from database.session import get_db 
from crud.plan import  get_all_plans , get_plans_cache_metadata
from schemas.plan import PlanResponse
import hashlib
import json


router = APIRouter()


def make_etag(count: int, last_updated) -> str:
    """Generates an ETag based on table metadata (count and last updated time)."""
    if not count or not last_updated:
        return "empty-db"
    raw_state = f"{count}-{last_updated.isoformat()}"
    return hashlib.md5(raw_state.encode()).hexdigest()



@router.get("/", response_model=list[PlanResponse])
def list_plans(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    # 1. Fetch lightweight metadata
    meta = get_plans_cache_metadata(db)
    last_updated = meta["last_updated"]
    
    # 2. Generate ETag instantly
    etag = make_etag(meta["count"], last_updated)
    
    client_etag = request.headers.get("if-none-match", "").strip('"')

    # 3. Check cache condition
    if client_etag == etag:
        return Response(
            status_code=HTTP_304_NOT_MODIFIED,
            headers={
                "ETag": f'"{etag}"',
                # FORCE the browser to revalidate this 304 response next time too
                "Cache-Control": "no-cache", 
            }
        )

    # 4. Cache miss: Fetch full payload
    plans = get_all_plans(db)
    
    # 5. Attach headers and return
    response.headers["ETag"] = f'"{etag}"'
    # FORCE the browser to always check the server using ETags
    response.headers["Cache-Control"] = "no-cache"
    
    if last_updated:
        response.headers["Last-Modified"] = last_updated.strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

    return plans