import uuid
import re
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from database.session import get_db
from ..dependencies import get_current_user
from models import User  
from crud.files import (
    upload_to_r2,
    update_files,
    build_feasibility_pdf,
    FileRecordNotFoundError,
    FileAccessForbiddenError,
)
from crud.request import create_request, get_existing_request
from r2_client import s3
from config import settings
from schemas.request import FeasibilityRequest 
from schemas.FileResponse import FileResponse
from api.rate_limiter import limiter


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

router = APIRouter(tags=["files"])


@router.post("/operational_partnership/submit")
@limiter.limit("5/hour")
def submit_operational_partnership(
    request: Request,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if get_existing_request(db, user.id, "operational_partnership"):
        raise HTTPException(409, "You already have an operational partnership request")

    if len(files) > 8:
        raise HTTPException(400, "Maximum 8 PDFs allowed")

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
    request = create_request(db=db, user_id=user.id, service_type="operational_partnership")

    uploaded_files = []
    try:
        for file, size in validated_files:
            file_id = str(uuid.uuid4())
            file_key = f"{user.id}/{file_id}.pdf"

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
        print(f"Background feasibility study upload failed: {e}")
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





@router.put("/operational_partnership/files/{file_id}", response_model=FileResponse)
@limiter.limit("10/hour")
async def update_operational_partnership_file(
    request: Request,
    file_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_bytes = await file.read()
    sanitized_filename = sanitize_filename(file.filename)

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
        raise HTTPException(status_code=500, detail=str(e))

    return updated