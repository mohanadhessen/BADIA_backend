import io
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from database.session import get_db
from ..dependencies import get_current_user
from models import User  
from crud.files import create_file, delete_file, update_file
from r2_clint import s3
from config import settings
from schemas.files import FeasibilityRequest 


R2_BUCKET = settings.R2_BUCKET

router = APIRouter(tags=["files"])


# =====================================================================
# 1. UPLOAD FILES
# =====================================================================
@router.post("/Operational_Partnership/submit")
def submit_Operational_Partnership(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    if len(files) > 8:
        raise HTTPException(400, "Maximum 8 PDFs allowed")

    uploaded_files = []
    MAX_SIZE = 10 * 1024 * 1024

    for file in files:
        if not file.filename:
            raise HTTPException(400, "Empty file")

        if not file.content_type or "pdf" not in file.content_type.lower():
            raise HTTPException(400, "Only PDF allowed")

        # Stream check size safely
        file.file.seek(0)
        size = 0
        for chunk in iter(lambda: file.file.read(1024 * 1024), b""):
            size += len(chunk)
            if size > MAX_SIZE:
                raise HTTPException(413, f"{file.filename} is too large")

        file.file.seek(0)
        file_id = str(uuid.uuid4())
        file_key = f"{user.id}/{file_id}.pdf"

        try:
            s3.upload_fileobj(
                file.file,
                R2_BUCKET,
                file_key,
                ExtraArgs={
                    "ContentType": "application/pdf"
                }
            )
        
        except Exception as e:
            raise HTTPException(500, f"Upload failed: {str(e)}")
        
        db_file = create_file(
            db=db,
            user_id=user.id,
            file_key=file_key,
            file_id=file_id,
            filename=file.filename,
            content_type=file.content_type,
            size=size,
            service_type="operational_partnership",
        )
        
        uploaded_files.append({
            "file_id": db_file.file_id,
            "filename": db_file.filename,
            "size": db_file.size,
            "file_key": db_file.file_key
        })
    return {
        "message": "Files uploaded successfully",
        "files": uploaded_files
    }





@router.post("/feasibility/submit")
def submit_feasibility_study(
    payload: FeasibilityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    text_content = (
        f"FEASIBILITY STUDY APPLICATION DATA\n"
        f"====================================\n"
        f"Applicant Email: {current_user.email}\n"
        f"Company Name: {current_user.company_name}\n"
        f"Phone Contact: {current_user.phone or '—'}\n\n"
        f"Estimated Project Cost: {payload.estimated_cost} KWD\n"
        f"Source of Funding: {payload.funding_source}\n\n"
        f"Detailed Project Description:\n"
        f"-----------------------------\n"
        f"{payload.project_description}\n"
    )

    text_bytes = text_content.encode("utf-8")
    file_size = len(text_bytes)

    file_id = str(uuid.uuid4())
    file_key = f"feasibility-studies/{current_user.id}/{file_id}.txt"
    filename = f"feasibility_study_{file_id}.txt"

    try:
        s3.upload_fileobj(
            io.BytesIO(text_bytes),
            settings.R2_BUCKET,
            file_key,
            ExtraArgs={
                "ContentType": "text/plain"
            }
        )

        created_file = create_file(
            db=db,
            user_id=current_user.id,
            file_key=file_key,
            file_id=file_id,
            filename=filename,
            content_type="text/plain",
            size=file_size,
            service_type="feasibility_study",
            status="pending",
        )

        return {
            "status": "success",
            "message": "Feasibility request submitted successfully",
            "file_id": created_file.file_id,
            "file_key": created_file.file_key
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Cloud deployment operational failure: {str(e)}"
        )
    

