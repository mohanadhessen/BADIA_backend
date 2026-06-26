from fastapi import APIRouter, Depends, HTTPException, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import sentry_sdk
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from models.request import Request as DBRequest
from crud.request import get_request_by_id, delete_request, admin_get_all_requests, update_request_status, get_requests_by_user_email
from email_service import send_request_status_email
from schemas.admin import StatusUpdate
from schemas.request import AdminRequestResponse
from models.user_file import UserFile
from r2_client import s3
from config import settings
from crud.dashboard_metrics import refresh_requests_metrics
from cache.requests import bump_global_requests_version , bump_user_requests_version, get_global_requests_version
from cache.etags import make_etag, check_etag
R2_BUCKET = settings.R2_BUCKET

router = APIRouter(
    prefix="",
    tags=["Admin - Requests"],
    dependencies=[Depends(require_admin)]
)

@router.get("/requests")
@limiter.limit("60/minute")
def get_all_requests(
    request: Request,
    response: Response,
    page: int = 1,
    limit: int = 25,
    q: str | None = None,
    type: str | None = None,
    status: str | None = None,
    plan: str | None = None,
    sort: str = "newest",
    db: Session = Depends(get_db)
):
    version = get_global_requests_version()
    etag_str = f"{version}:{page}:{limit}:{q}:{type}:{status}:{plan}:{sort}"
    etag = make_etag(etag_str)
    
    if check_etag(request, response, etag):
        return {}

    data = admin_get_all_requests(
        db=db,
        page=page,
        limit=limit,
        q=q,
        type=type,
        status=status,
        plan=plan,
        sort=sort
    )
    return data


@router.get("/requests/by-email", response_model=list[AdminRequestResponse])
@limiter.limit("60/minute")
def get_requests_by_email_endpoint(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
):
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email query parameter is required"
        )
    requests = get_requests_by_user_email(db, email)
    return requests


@router.get("/requests/{request_id}/files/{file_id}")
@limiter.limit("30/minute")
def download_request_file(
    request: Request,
    request_id: int, 
    file_id: str, 
    db: Session = Depends(get_db)
):
    req = get_request_by_id(db=db, request_id=request_id)

    if not req:
        raise HTTPException(404, "Request not found")

    db_file = db.query(UserFile).filter(
        UserFile.file_id == file_id,
        UserFile.request_id == request_id
    ).first()

    if not db_file:
        raise HTTPException(404, "File not found")

    try:
        inline_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": R2_BUCKET,
                "Key": db_file.file_key,
                "ResponseContentDisposition": f'inline; filename="{db_file.filename}"',
            },
            ExpiresIn=300
        )
        download_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": R2_BUCKET,
                "Key": db_file.file_key,
                "ResponseContentDisposition": f'attachment; filename="{db_file.filename}"',
            },
            ExpiresIn=300
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(500, f"Could not generate download URL: {str(e)}")

    return JSONResponse({
        "url": inline_url,
        "download_url": download_url,
        "filename": db_file.filename
    })


@router.patch("/requests/{request_id}/status")
@limiter.limit("30/minute")
def update_request_status_endpoint(
    request: Request,
    request_id: str,
    body: StatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    updated_request = update_request_status(
        db=db,
        request_id=request_id,
        new_status=body.status.value
    )

    if not updated_request:
        raise HTTPException(
            status_code=404,
            detail="Request not found"
        )
    bump_user_requests_version(updated_request.user_id)
    bump_global_requests_version()
    user_email = updated_request.user.email
    user_name = f"{updated_request.user.first_name or ''} {updated_request.user.last_name or ''}".strip()
    service_type = updated_request.service_type
    is_approved = body.status.value  


    background_tasks.add_task(
        send_request_status_email,
        user_email,
        user_name,
        service_type,
        is_approved
    )

    refresh_requests_metrics(db)
    return updated_request


@router.delete("/requests/{request_id}")
@limiter.limit("30/minute")
def admin_delete_request(
    request: Request,
    request_id: str,
    db: Session = Depends(get_db)
):
    req = get_request_by_id(db=db, request_id=request_id)
    if req:
        bump_user_requests_version(req.user_id)
    bump_global_requests_version()
    result = delete_request(
        db=db,
        request_id=request_id,
        s3=s3,
        bucket=settings.R2_BUCKET
    )

    if not result:
        raise HTTPException(status_code=404, detail="Request not found")

    refresh_requests_metrics(db)
    return {
        "message": "Request deleted successfully",
        **result
    }
