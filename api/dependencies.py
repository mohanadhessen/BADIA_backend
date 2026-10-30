from fastapi import Cookie, Depends, HTTPException, Request, status
from jwt import PyJWTError as JWTError
from sqlalchemy.ext.asyncio import AsyncSession 
from database.session import get_db
from models import User
from security import decode_access_token
from config import settings
from crud.user import get_user_by_id

async def get_current_user(
    request: Request,
    db: AsyncSession =  Depends(get_db),
    access_token: str | None = Cookie(default=None, alias=settings.ACCESS_TOKEN_COOKIE_NAME),
):
    credentials_exception = HTTPException(  status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials",headers={"WWW-Authenticate": "Bearer"})

    if not access_token:
        raise credentials_exception

    try:
        payload = decode_access_token(token=access_token)
        if payload.get("type") != "access":raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token type")
    
        user_id = payload.get("sub")

        if not user_id:
            raise credentials_exception
        
            
    except JWTError:
        raise credentials_exception

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise credentials_exception

    user = get_user_by_id(db,user_id)
    if user is None:
        raise credentials_exception

    return user



async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user