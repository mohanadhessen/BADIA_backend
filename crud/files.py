from models import UserFile
from sqlalchemy.orm import Session , joinedload


def create_file(
    db: Session,
    user_id: int,
    file_key: str,
    file_id: str,
    service_type: str,
    status: str = "pending",
    filename: str | None = None,
    content_type: str | None = None,
    size: int | None = None,
):
    new_file = UserFile(
        user_id=user_id,
        file_key=file_key,
        file_id=file_id,
        service_type=service_type,
        status=status,
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
    user_id: int | None = None,
    file_key: str | None = None,
    filename: str | None = None,
    content_type: str | None = None,
    size: int | None = None,
    service_type: str | None = None,
    status: str | None = None,
):
    file = db.query(UserFile).filter(UserFile.file_id == file_id).first()

    if not file:
        return None

    update_data = {
        "user_id": user_id,
        "file_key": file_key,
        "filename": filename,
        "content_type": content_type,
        "size": size,
        "service_type": service_type,
        "status": status,
    }

    for key, value in update_data.items():
        if value is not None:
            setattr(file, key, value)

    db.commit()
    db.refresh(file)

    return file



def delete_file(
    db: Session,
    file_id: str
):
    file = db.query(UserFile).filter(UserFile.file_id == file_id).first()

    if not file:
        return False

    db.delete(file)
    db.commit()

    return True