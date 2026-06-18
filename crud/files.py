from models.UserFile import UserFile
from sqlalchemy import func
from sqlalchemy.orm import Session 
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import io
from reportlab.lib.pagesizes import letter
import uuid
from crud.request import Request
import sentry_sdk
class FileRecordNotFoundError(Exception):
    pass


class FileAccessForbiddenError(Exception):
    pass




def create_file(
    db: Session,
    request_id: int,
    file_key: str,
    file_id: str,
    filename: str,
    content_type: str,
    size: int,
):
    new_file = UserFile(
        request_id=request_id,
        file_key=file_key,
        file_id=file_id,
        filename=filename,
        content_type=content_type,
        size=size,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return new_file


def update_file(
    db: Session,
    file_id: str,
    file_key: str | None = None,
    filename: str | None = None,
    content_type: str | None = None,
    size: int | None = None,
):
    file = db.query(UserFile).filter(UserFile.file_id == file_id).first()
    if not file:
        return None

    update_data = {
        "file_key": file_key,
        "filename": filename,
        "content_type": content_type,
        "size": size,
    }

    for key, value in update_data.items():
        if value is not None:
            setattr(file, key, value)
    db.commit()
    db.refresh(file)
    return file



def delete_file(db: Session, file_id: str) -> bool:
    file = db.query(UserFile).filter(UserFile.file_id == file_id).first()
    if not file:
        return False
    if file.request:
        file.request.updated_at = func.now()
    db.delete(file)
    db.commit()
    return True






def upload_to_r2(
    db,               
    s3,         
    file_obj,          
    bucket_name: str,
    file_key: str,
    filename: str,
    content_type: str,
    size: int,
    request_id: int,
    file_id: str = None
):
    
    if not file_id:
        file_id = str(uuid.uuid4())


    s3.upload_fileobj(
        file_obj,
        bucket_name,
        file_key,
        ExtraArgs={"ContentType": content_type}
    )


    db_file = create_file(
        db=db,
        request_id=request_id,
        file_key=file_key,
        file_id=file_id,
        filename=filename,
        content_type=content_type,
        size=size,
    )
    
    return db_file


def delete_from_r2(
    s3,
    bucket_name: str,
    file_key: str
):
    try:
        s3.delete_object(
            Bucket=bucket_name,
            Key=file_key
        )
        return True
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return False
    



def update_files(
    s3,
    bucket_name: str,
    db_session,
    file_id: str,
    new_file_bytes: bytes,
    new_filename: str,
    new_content_type: str,
    user_id: str,          
):
    file_record = (
        db_session.query(UserFile)
        .filter(UserFile.file_id == file_id)
        .first()
    )

    if not file_record:
        raise FileRecordNotFoundError("File not found")
    if file_record.request.user_id != user_id:        
      raise FileAccessForbiddenError("Forbidden")


    s3.put_object(
        Bucket=bucket_name,
        Key=file_record.file_key,
        Body=new_file_bytes,
        ContentType=new_content_type,
    )

    file_record.filename = new_filename
    file_record.size = len(new_file_bytes)
    file_record.content_type = new_content_type

    if file_record.request:
        file_record.request.updated_at = func.now()

    db_session.commit()

    return file_record






def build_feasibility_pdf(current_user, payload) -> io.BytesIO:
    pdf_buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"], fontSize=14, spaceAfter=6
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"], fontSize=10, textColor="grey"
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"], fontSize=10, spaceAfter=8
    )

    story = [
        Paragraph("FEASIBILITY STUDY APPLICATION DATA", title_style),
        Spacer(1, 0.2 * inch),

        Paragraph("Applicant Email", label_style),
        Paragraph(current_user.email, body_style),

        Paragraph("Company Name", label_style),
        Paragraph(current_user.company_name or "—", body_style),

        Paragraph("Phone Contact", label_style),
        Paragraph(current_user.phone or "—", body_style),

        Spacer(1, 0.1 * inch),

        Paragraph("Estimated Project Cost", label_style),
        Paragraph(f"{payload.estimated_cost} KWD", body_style),

        Paragraph("Source of Funding", label_style),
        Paragraph(payload.funding_source, body_style),

        Spacer(1, 0.1 * inch),

        Paragraph("Detailed Project Description", label_style),
        Paragraph(payload.project_description, body_style),
    ]

    doc.build(story)
    pdf_buffer.seek(0)

    return pdf_buffer