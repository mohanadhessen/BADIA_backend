import io
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from database.session import get_db
from ..dependencies import get_current_user
from models import User  
from crud.files import create_file
from crud.request import create_request , get_existing_request
from r2_client import s3
from config import settings
from schemas.files import FeasibilityRequest 
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
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
    if get_existing_request(db, user.id, "operational_partnership"):
        raise HTTPException(409, "You already have an operational partnership request")

    if len(files) > 8:
        raise HTTPException(400, "Maximum 8 PDFs allowed")

    MAX_SIZE = 10 * 1024 * 1024
    validated_files = []

    for file in files:
        if not file.filename:
            raise HTTPException(400, "Empty file")
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

    # ── Create request first ────────────────────────────────────
    request = create_request(db=db, user_id=user.id, service_type="operational_partnership")

    uploaded_files = []
    try:
        for file, size in validated_files:
            file_id = str(uuid.uuid4())
            file_key = f"{user.id}/{file_id}.pdf"

            try:
                s3.upload_fileobj(
                    file.file, R2_BUCKET, file_key,
                    ExtraArgs={"ContentType": "application/pdf"}
                )
            except Exception as e:
                raise HTTPException(500, f"Upload failed: {str(e)}")

            db_file = create_file(
                db=db,
                request_id=request.id,
                file_key=file_key,
                file_id=file_id,
                filename=file.filename,
                content_type=file.content_type,
                size=size,
            )
            uploaded_files.append({
                "file_id": db_file.file_id,
                "filename": db_file.filename,
                "size": db_file.size,
                "file_key": db_file.file_key
            })

    except HTTPException:
        db.delete(request)
        db.commit()
        raise

    return {
        "message": "Files uploaded successfully",
        "request_id": request.request_id,
        "files": uploaded_files
    }



@router.post("/feasibility/submit")
def submit_feasibility_study(
    payload: FeasibilityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if get_existing_request(db, current_user.id, "feasibility_study"):
        raise HTTPException(409, "You already have a feasibility study request")

    request = create_request(
        db=db,
        user_id=current_user.id,
        service_type="feasibility_study"
    )

    file_id = str(uuid.uuid4())

    try:
        # ── Create PDF in memory ───────────────────────────────
        pdf_buffer = io.BytesIO()
        p = canvas.Canvas(pdf_buffer, pagesize=letter)

        y = 750

        lines = [
            "FEASIBILITY STUDY APPLICATION DATA",
            "====================================",
            "",
            f"Applicant Email: {current_user.email}",
            f"Company Name: {current_user.company_name}",
            f"Phone Contact: {current_user.phone or '—'}",
            "",
            f"Estimated Project Cost: {payload.estimated_cost} KWD",
            f"Source of Funding: {payload.funding_source}",
            "",
            "Detailed Project Description:",
            "-----------------------------",
            payload.project_description,
        ]

        for line in lines:
            # basic wrap protection
            safe_line = str(line)
            p.drawString(50, y, safe_line[:120])
            y -= 20

            if y < 50:
                p.showPage()
                y = 750

        p.save()
        pdf_buffer.seek(0)

        pdf_bytes = pdf_buffer.read()

        file_key = f"feasibility-studies/{current_user.id}/{file_id}.pdf"


        s3.upload_fileobj(
            io.BytesIO(pdf_bytes),
            settings.R2_BUCKET,
            file_key,
            ExtraArgs={"ContentType": "application/pdf"}
        )

        created_file = create_file(
            db=db,
            request_id=request.id,
            file_id=file_id,
            file_key=file_key,
            filename=f"feasibility_study_{file_id}.pdf",
            content_type="application/pdf",
            size=len(pdf_bytes),
        )

        return {
            "status": "success",
            "message": "Feasibility request submitted successfully",
            "request_id": request.request_id,
            "file_id": created_file.file_id,
        }

    except HTTPException:
        raise

    except Exception as e:
        db.delete(request)
        db.commit()
        raise HTTPException(500, f"Submission failed: {str(e)}")



