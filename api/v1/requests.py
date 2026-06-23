import uuid
import re
from typing import List
import sentry_sdk
from fastapi.responses import JSONResponse
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request, BackgroundTasks, Response
from sqlalchemy.orm import Session
from database.session import get_db
from ..dependencies import get_current_user
from models import User  
from models.user_file import UserFile
from crud.files import (
    upload_to_r2,
    update_files,
    build_feasibility_pdf,
    FileRecordNotFoundError,
    FileAccessForbiddenError,
)
from crud.request import (
    create_request,
    get_existing_request,
    get_request_by_id,
    delete_request,
    get_user_requests
)
from r2_client import s3
from config import settings
from schemas.request import FeasibilityRequest 
from schemas.FileResponse import FileResponse
from api.rate_limiter import limiter
from cache.requests import bump_user_requests_version, get_user_requests_version, bump_global_requests_version
from cache.etags import make_etag, check_etag


R2_BUCKET = settings.R2_BUCKET

def sanitize_filename(filename: str) -> str:
    if not filename:
        return "unnamed.pdf"
    # Keep alphanumeric, dot, dash, underscore
    safe = re.sub(r'[^a-zA-Z0-9.\-_]', '_', filename)
    # Prevent directory traversal
    safe = safe.lstrip('.').strip()
    if not safe:
        return "file.pdf"
    return safe[:100]

router = APIRouter(tags=["Requests"])


# -------------------------
# GET (read)
# -------------------------
@router.get("")
@limiter.limit("60/minute")
def get_my_requests(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    version = get_user_requests_version(current_user.id)

    if version == 0:
        bump_user_requests_version(current_user.id)
        version = 1

    etag = make_etag(version)

    if check_etag(request, response, etag):
        return []

    requests = get_user_requests(db=db, user_id=current_user.id)

    formatted_requests = [
        {
            "id": req.id,
            "service_type": req.service_type,
            "status": req.status,
            "created_at": req.created_at,
            "files": [
                {
                    "file_id": f.file_id,
                    "filename": f.filename,
                    "created_at": f.created_at
                }
                for f in req.files
            ] if req.files else []
        }
        for req in requests
    ]

    return {
        "status": "success",
        "requests": formatted_requests
    }


@router.get("/{request_id}/files/{file_id}")
@limiter.limit("30/minute")
def download_my_file(
    request: Request,
    request_id: int,
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    request_obj = get_request_by_id(db=db, request_id=request_id)
    if not request_obj or request_obj.user_id != current_user.id:
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


# -------------------------
# POST (create)
# -------------------------
@router.post("/partnership/submit")
@limiter.limit("5/hour")
def submit_partnership(
    request: Request,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    if get_existing_request(db, current_user.id, "partnership"):
        raise HTTPException(409, "You already have a partnership request")

    if len(files) > 8:
        raise HTTPException(400, "Maximum 8 PDFs allowed")
    bump_user_requests_version(current_user.id)
    bump_global_requests_version()
    MAX_SIZE = 10 * 1024 * 1024
    validated_files = []

    for file in files:
        if not file.filename:
            raise HTTPException(400, "Empty file")
            
        file.filename = sanitize_filename(file.filename)
        if not file.content_type or "pdf" not in file.content_type.lower():
            raise HTTPException(400, "Only PDF allowed")

        file.file.seek(0)
        size = 0
        for chunk in iter(lambda: file.file.read(1024 * 1024), b""):
            size += len(chunk)
            if size > MAX_SIZE:
                raise HTTPException(413, f"{file.filename} is too large")

        file.file.seek(0)
        validated_files.append((file, size))

    # Create request first
    request = create_request(db=db, user_id=current_user.id, service_type="partnership")

    uploaded_files = []
    try:
        for file, size in validated_files:
            file_id = str(uuid.uuid4())
            file_key = f"{current_user.id}/{file_id}.pdf"

            # Delegate upload and metadata logging to CRUD
            db_file = upload_to_r2(
                db=db,
                s3=s3,
                file_obj=file.file,
                bucket_name=R2_BUCKET,
                file_key=file_key,
                filename=file.filename,
                content_type=file.content_type,
                size=size,
                request_id=request.id,
                file_id=file_id
            )

            uploaded_files.append({
                "file_id": db_file.file_id,
                "filename": db_file.filename,
                "size": db_file.size,
                "file_key": db_file.file_key
            })

    except Exception as e:
        db.rollback()
        db.delete(request)
        db.commit()
        if isinstance(e, HTTPException):
            raise
        sentry_sdk.capture_exception(e)
        raise HTTPException(500, f"Upload failed: {str(e)}")

    return {
        "message": "Files uploaded successfully",
        "request_id": request.id,
        "files": uploaded_files
    }


def process_feasibility_study_background(
    current_user_id: int,
    current_user_email: str,
    current_user_company_name: str | None,
    current_user_phone: str | None,
    payload_dict: dict,
    request_id: int,
    file_id: str
):
    from database.session import SessionLocal
    from models.request import Request as DBRequest
    from crud.files import build_feasibility_pdf, upload_to_r2
    from r2_client import s3
    from config import settings

    db = SessionLocal()
    try:
        class SimpleUser:
            def __init__(self, email, company_name, phone):
                self.email = email
                self.company_name = company_name
                self.phone = phone

        class SimplePayload:
            def __init__(self, data):
                self.estimated_cost = data.get("estimated_cost")
                self.funding_source = data.get("funding_source")
                self.project_description = data.get("project_description")

        user_obj = SimpleUser(current_user_email, current_user_company_name, current_user_phone)
        payload_obj = SimplePayload(payload_dict)

        pdf_buffer = build_feasibility_pdf(user_obj, payload_obj)
        pdf_bytes = pdf_buffer.getvalue()
        file_key = f"feasibility-studies/{current_user_id}/{file_id}.pdf"

        upload_to_r2(
            db=db,
            s3=s3,
            file_obj=pdf_buffer,
            bucket_name=settings.R2_BUCKET,
            file_key=file_key,
            filename=f"feasibility_study_{file_id}.pdf",
            content_type="application/pdf",
            size=len(pdf_bytes),
            request_id=request_id,
            file_id=file_id
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        req = db.query(DBRequest).filter(DBRequest.id == request_id).first()
        if req:
            db.delete(req)
            db.commit()
    finally:
        db.close()


@router.post("/feasibility/submit")
@limiter.limit("5/hour")
def submit_feasibility_study(
    request: Request,
    payload: FeasibilityRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if get_existing_request(db, current_user.id, "feasibility_study"):
        raise HTTPException(409, "You already have a feasibility study request")
    bump_user_requests_version(current_user.id)
    bump_global_requests_version()
    new_request = create_request(
        db=db,
        user_id=current_user.id,
        service_type="feasibility_study"
    )

    file_id = str(uuid.uuid4())

    payload_dict = {
        "estimated_cost": payload.estimated_cost,
        "funding_source": payload.funding_source,
        "project_description": payload.project_description
    }

    background_tasks.add_task(
        process_feasibility_study_background,
        current_user.id,
        current_user.email,
        current_user.company_name,
        current_user.phone,
        payload_dict,
        new_request.id,
        file_id
    )

    return {
        "status": "success",
        "message": "Feasibility request submitted successfully",
        "request_id": new_request.id,
        "file_id": file_id,
    }


# -------------------------
# PUT (update)
# -------------------------
@router.put("/partnership/files/{file_id}", response_model=FileResponse)
@limiter.limit("10/hour")
async def update_partnership_file(
    request: Request,
    file_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_bytes = await file.read()
    sanitized_filename = sanitize_filename(file.filename)
    bump_user_requests_version(current_user.id)
    bump_global_requests_version()
    try:
        updated = update_files(
            s3=s3,
            bucket_name=settings.R2_BUCKET,
            db_session=db,
            file_id=file_id,
            new_file_bytes=file_bytes,
            new_filename=sanitized_filename,
            new_content_type=file.content_type,
            user_id=current_user.id,
        )
    except FileAccessForbiddenError:
        raise HTTPException(status_code=403, detail="You do not own this file")
    except FileRecordNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=str(e))

    return updated


@router.put("/feasibility/files/{file_id}", response_model=FileResponse)
@limiter.limit("10/hour")
async def update_feasibility_file(
    request: Request,
    file_id: str,
    payload: FeasibilityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pdf_buffer = build_feasibility_pdf(current_user, payload)
    pdf_bytes = pdf_buffer.read()
    bump_user_requests_version(current_user.id)
    bump_global_requests_version()
    try:
        updated = update_files(
            s3=s3,
            bucket_name=settings.R2_BUCKET,
            db_session=db,
            file_id=file_id,
            new_file_bytes=pdf_bytes,
            new_filename="feasibility_study.pdf",
            new_content_type="application/pdf",
            user_id=current_user.id
        )
    except FileAccessForbiddenError:
        raise HTTPException(status_code=403, detail="You do not own this file")
    except FileRecordNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=str(e))

    return updated


# -------------------------
# DELETE (remove)
# -------------------------
@router.delete("/{request_id}")
@limiter.limit("10/minute")
def delete_my_request(
    request: Request,
    request_id: int,  
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    request_obj = get_request_by_id(db=db, request_id=request_id)
    
    if not request_obj:
        raise HTTPException(
            status_code=404,
            detail="Request not found"
        )

    if request_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this request"
        )
    bump_user_requests_version(current_user.id)
    bump_global_requests_version()

    deletion_result = delete_request(
        db=db,
        request_id=request_id,
        s3=s3,
        bucket=R2_BUCKET
    )

    return {
        "status": "success",
        "message": "Request and associated storage objects deleted successfully",
        "details": deletion_result
    }