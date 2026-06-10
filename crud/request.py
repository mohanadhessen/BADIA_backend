from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from models.request import Request
from sqlalchemy.orm import Session 
from sqlalchemy.exc import IntegrityError
import uuid



def get_existing_request(db: Session, user_id: int, service_type: str) -> Request | None:
    return db.query(Request).filter(
        Request.user_id == user_id,
        Request.service_type == service_type
    ).first()



def create_request(db: Session, user_id: int, service_type: str) -> Request:
    request = Request(
        user_id=user_id,
        request_id=str(uuid.uuid4()),
        service_type=service_type,
        status="pending"
    )
    db.add(request)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "You already have a request for this service")
    db.refresh(request)
    return request


def get_request_by_id(db: Session, request_id: str) -> Request | None:
    return db.query(Request).filter(Request.id == request_id).first()


def get_user_requests(db: Session, user_id: int):

    return (
        db.query(Request)
        .options(joinedload(Request.files))
        .filter(Request.user_id == user_id)
        .order_by(Request.created_at.desc())
        .all()
    )



def update_request_status(
    db: Session,
    request_id: str,
    new_status: str
) -> Request | None:
    request = get_request_by_id(db, request_id)
    if not request:
        return None
    request.status = new_status
    db.commit()
    db.refresh(request)
    return request






def delete_s3_file(s3, bucket: str, key: str):
    if not key:
        return

    s3.delete_object(
        Bucket=bucket,
        Key=key
    )




def delete_request(
    db: Session,
    request_id: str,
    s3,
    bucket: str
):
    request = get_request_by_id(db, request_id)

    if not request:
        return None

    file_keys = [f.file_key for f in request.files if f.file_key]

    for key in file_keys:
        delete_s3_file(
            s3=s3,
            bucket=bucket,
            key=key
        )

    db.delete(request)
    db.commit()

    return {
        "request_id": request_id,
        "deleted_files": len(file_keys)
    }



def admin_get_all_requests(db: Session, page: int = 1, limit: int = 25):

    offset = (page - 1) * limit

    requests = (
        db.query(Request)
        .options(
            joinedload(Request.user),
            joinedload(Request.files)
        )
        .order_by(Request.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "request_id": r.id,
            "user_id": r.user_id,
            "service_type": r.service_type,
            "status": r.status,
            "created_at": r.created_at,
            "updated_at": r.updated_at,

            "user": {
                "id": r.user.id,
                "email": r.user.email,
                "first_name": r.user.first_name,
                "last_name": r.user.last_name,
                "company_name": r.user.company_name,
                "phone": r.user.phone,
            } if r.user else None,

            "files": [
                {
                    "id": f.id,
                    "file_id": f.file_id,
                    "filename": f.filename,
                    "file_key": f.file_key,
                    "content_type": f.content_type,
                    "size": f.size,
                    "created_at": f.created_at,
                }
                for f in r.files
            ]
        }
        for r in requests
    ]
