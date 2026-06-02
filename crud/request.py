from fastapi import HTTPException
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


def get_requests_by_user(
    db: Session,
    user_id: int,
    status: str | None = None,
    skip: int = 0,
    limit: int = 20
) -> list[Request]:
    query = db.query(Request).filter(Request.user_id == user_id)
    if status:
        query = query.filter(Request.status == status)
    return query.offset(skip).limit(limit).all()


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


def delete_request(db: Session, request_id: str) -> bool:
    request = get_request_by_id(db, request_id)
    if not request:
        return False
    db.delete(request)
    db.commit()
    return True



