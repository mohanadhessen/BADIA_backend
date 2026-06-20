from pwdlib import PasswordHash
import jwt
from datetime import datetime, timedelta, timezone
from config import settings
from fastapi import HTTPException, status , Response
import hashlib


SECRET_KEY = settings.TOKEN_SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


pwd = PasswordHash.recommended()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()




def hash_password(password: str) -> str:
    return pwd.hash(password)
def verify_password(password: str, hashed: str) -> bool:
    return pwd.verify(password, hashed)



def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])




def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)

    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt



def verify_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        
        # Enforce type constraints to block access tokens from exploiting this path
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type context",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    







def set_auth_cookies(response: Response, access_token: str, refresh_token: str, role: str = "") -> None:
    cookie_domain = settings.COOKIE_DOMAIN if settings.COOKIE_DOMAIN else None
    common = dict(
        domain=cookie_domain,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        httponly=True,
    )
    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **common,
    )
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=30 * 24 * 3600,   
        **common,
    )
    
    if role:
        response.set_cookie(
            key=settings.ROLE_COOKIE_NAME,
            value=role,
            max_age=30 * 24 * 3600,
            domain=cookie_domain,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            httponly=False,  
        )


def clear_auth_cookies(response: Response) -> None:
    cookie_domain = settings.COOKIE_DOMAIN if settings.COOKIE_DOMAIN else None
    for name in [
        settings.ACCESS_TOKEN_COOKIE_NAME,
        settings.REFRESH_TOKEN_COOKIE_NAME,
        settings.ROLE_COOKIE_NAME,
    ]:
        response.delete_cookie(
            key=name,
            domain=cookie_domain,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
        )
