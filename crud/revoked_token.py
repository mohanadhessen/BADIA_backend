from sqlalchemy.orm import Session
from models import RevokedToken
from security import hash_token


def get_revoked_token(db: Session, token: str):
    hashed_token = hash_token(token)
    res = db.query(RevokedToken).filter(
        RevokedToken.token == hashed_token
    ).first()
    if res:
        return res
    # Fallback to check raw token (for legacy revoked tokens already in the DB)
    return db.query(RevokedToken).filter(
        RevokedToken.token == token
    ).first()


def create_revoked_token(db: Session, token: str):
    hashed_token = hash_token(token)
    revoked = RevokedToken(token=hashed_token)
    db.add(revoked)
    db.commit()
    db.refresh(revoked)
    return revoked


def is_token_revoked(db: Session, token: str) -> bool:
    hashed_token = hash_token(token)
    if db.query(RevokedToken).filter(
        RevokedToken.token == hashed_token
    ).first() is not None:
        return True
    # Fallback to check raw token (for legacy revoked tokens already in the DB)
    return db.query(RevokedToken).filter(
        RevokedToken.token == token
    ).first() is not None



