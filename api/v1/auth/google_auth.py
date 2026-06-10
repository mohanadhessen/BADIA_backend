from fastapi import APIRouter, Depends, HTTPException , Request
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from sqlalchemy.orm import Session
from database.session import get_db
from crud.user import get_user_by_email , create_new_user
from config import settings
import httpx
from security import create_access_token , create_refresh_token
from api.rate_limiter import limiter



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
async def auth_google_callback(request: Request, db: Session = Depends(get_db), remember_me: bool = True):
    code = request.query_params.get("code")

    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    async with httpx.AsyncClient() as client:
        # 1. Exchange code → token
        token_res = await client.post(
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

        # 2. Get user info from Google
        user_res = await client.get(
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

    # Prepare token payload
    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role
    }

    # Generate backend application tokens
    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(data=token_payload, remember_me=remember_me)
    
    # -------------------------------------------------------------------------
    # FIXED: Redirect to Frontend Account Page instead of returning JSON
    # -------------------------------------------------------------------------
    # Replace this with your actual frontend URL (e.g., from your settings/config)

    
    # Construct redirect URL appending tokens as query parameters
    redirect_url = (
        f"{FRONTEND_ACCOUNT_URL}"
        f"?access_token={access_token}"
        f"&refresh_token={refresh_token}"
    )
    
    return RedirectResponse(url=redirect_url)