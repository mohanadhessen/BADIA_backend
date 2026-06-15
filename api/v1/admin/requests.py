from fastapi import APIRouter, Depends, HTTPException, Request , BackgroundTasks, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from api.etag import compute_etag, check_etag, compute_db_etag
from models.request import Request as DBRequest
from crud.request import get_request_by_id, delete_request, admin_get_all_requests, update_request_status
from email_service import send_request_status_email
from schemas.admin import StatusUpdate
from models.UserFile import UserFile
from r2_client import s3
from config import settings

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
    db: Session = Depends(get_db)
):
    etag = compute_db_etag(db, DBRequest, page=page, limit=limit, order_by=DBRequest.created_at.desc())
    check_etag(request, etag)

    data = admin_get_all_requests(
        db=db,
        page=page,
        limit=limit
    )
    response.headers["ETag"] = etag
    return data

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

    return updated_request


@router.delete("/requests/{request_id}")
@limiter.limit("30/minute")
def admin_delete_request(
    request: Request,
    request_id: str,
    db: Session = Depends(get_db)
):
    result = delete_request(
        db=db,
        request_id=request_id,
        s3=s3,
        bucket=settings.R2_BUCKET
    )

    if not result:
        raise HTTPException(status_code=404, detail="Request not found")

    return {
        "message": "Request deleted successfully",
        **result
    }

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
        raise HTTPException(500, f"Could not generate download URL: {str(e)}")

    return JSONResponse({
        "url": inline_url,
        "download_url": download_url,
        "filename": db_file.filename
    })
