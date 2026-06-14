from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from sqlalchemy.orm import Session
from database.session import get_db
from crud.user import get_user_by_email, create_new_user, get_user_by_id
from config import settings
import httpx
from security import create_access_token, create_refresh_token, set_auth_cookies, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from api.rate_limiter import limiter
from datetime import timedelta
from pydantic import BaseModel


http_client = httpx.AsyncClient()
router = APIRouter(tags=["OAuth"])



GOOGLE_AUTH_ENDPOINT     = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT    = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"

GOOGLE_CLIENT_ID     = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URL  = settings.GOOGLE_REDIRECT_URL
FRONTEND_ACCOUNT_URL = settings.FRONTEND_ACCOUNT_URL




@router.get("/google")
@limiter.limit("10/minute")
def login_google(request: Request):

    query_params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  GOOGLE_REDIRECT_URL,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "consent",
    }
    url = f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(query_params)}"
    return RedirectResponse(url)



@router.get("/google/callback")
@limiter.limit("10/minute")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get("code")

    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    # 1. Exchange code → token
    token_res = await http_client.post(
        GOOGLE_TOKEN_ENDPOINT,
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URL,
            "grant_type": "authorization_code",
        },
    )

    token_data = token_res.json()
    google_access_token = token_data.get("access_token")

    if not google_access_token:
        raise HTTPException(status_code=400, detail="No access token received from Google")

    # Optimize: extract user info directly from id_token to avoid an extra network call
    id_token = token_data.get("id_token")
    user_data = None
    if id_token:
        try:
            user_data = jwt.get_unverified_claims(id_token)
        except Exception:
            pass

    if not user_data:
        # 2. Get user info from Google (Fallback)
        user_res = await http_client.get(
            GOOGLE_USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {google_access_token}"},
        )
        
        if user_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info from Google")
            
        user_data = user_res.json()

    email = user_data.get("email")
    google_id = user_data.get("sub")
    first_name = user_data.get("given_name")
    last_name = user_data.get("family_name")
    avatar_url = user_data.get("picture")

    if not email:
        raise HTTPException(status_code=400, detail="Google account missing email address")

    existing_user = get_user_by_email(db, email)

    if existing_user:
        # If they exist but haven't linked Google yet, link it now
        if not existing_user.google_id:
            existing_user.google_id = google_id
            existing_user.avatar_url = avatar_url or existing_user.avatar_url
            db.commit()
            db.refresh(existing_user)
        user = existing_user
    else:
        # Create the new OAuth user
        user = create_new_user(
            db=db,
            email=email,
            first_name=first_name,
            last_name=last_name,
            google_id=google_id,
            avatar_url=avatar_url,
            auth_provider="google"
        )

    # Instead of setting cookies directly on a 302 redirect (which fails in Safari/Incognito due to 3rd-party cookie blocking),
    # we create a short-lived exchange token and pass it to the frontend via URL.
    exchange_token = create_access_token(data={"sub": str(user.id), "type": "exchange"}, expires_delta=timedelta(minutes=5))

    redirect_response = RedirectResponse(url=f"{FRONTEND_ACCOUNT_URL}?oauth_token={exchange_token}", status_code=302)
    return redirect_response


class ExchangeRequest(BaseModel):
    token: str

@router.post("/google/exchange")
@limiter.limit("20/minute")
def exchange_google_token(request: Request, response: Response, payload: ExchangeRequest, db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(payload.token, SECRET_KEY, algorithms=[ALGORITHM])
        if decoded.get("type") != "exchange":
            raise HTTPException(status_code=400, detail="Invalid token type")
            
        user_id = decoded.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token payload")
            
        user = get_user_by_id(db, int(user_id))
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
            
        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
        
        access_token = create_access_token(data=token_payload)
        refresh_token = create_refresh_token(data=token_payload)
        
        set_auth_cookies(response, access_token, refresh_token)
        
        return {
            "status": "success",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "company_name": user.company_name,
                "phone": user.phone,
                "avatar_url": user.avatar_url,
                "auth_provider": user.auth_provider,
                "created_at": user.created_at,
                "is_email_verified": user.is_email_verified,
            }
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid exchange token")