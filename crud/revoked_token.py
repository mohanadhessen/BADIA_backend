from sqlalchemy.orm import Session
from models import RevokedToken


def get_revoked_token(db: Session, token: str):
    return db.query(RevokedToken).filter(
        RevokedToken.token == token
    ).first()


def create_revoked_token(db: Session, token: str):
    revoked = RevokedToken(token=token)
    db.add(revoked)
    db.commit()
    db.refresh(revoked)
    return revoked


def is_token_revoked(db: Session, token: str) -> bool:
    return db.query(RevokedToken).filter(
        RevokedToken.token == token
    ).first() is not None


