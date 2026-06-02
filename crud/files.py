from models.user_file import user_file
from sqlalchemy.orm import Session 


def create_file(
    db: Session,
    request_id: int,
    file_key: str,
    file_id: str,
    filename: str,
    content_type: str,
    size: int,
):
    new_file = user_file(
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
    file = db.query(user_file).filter(user_file.file_id == file_id).first()
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
    file = db.query(user_file).filter(user_file.file_id == file_id).first()
    if not file:
        return False
    db.delete(file)
    db.commit()
    return True