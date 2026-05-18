from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer , OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import httpx
from urllib.parse import urlencode

from database.session import get_db
from models import UserSchema  # Ensure this matches your models file import
from security import hash_password  # If you generate internal JWTs, import that here too
from config import settings

app = FastAPI()

origins = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            
    allow_credentials=True,
    allow_methods=["*"],              
    allow_headers=["*"],              
)


# Pydantic schema for the incoming request
class UserRegister(BaseModel):
    company_name: str
    email: EmailStr
    password: str
    phone: str | None = None
class GoogleAuthPayload(BaseModel):
    token: str


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_company(user_in: UserRegister, db: Session = Depends(get_db)):
    # 1. Check if email is already taken
    existing_user = db.query(UserSchema).filter(UserSchema.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already registered to a company."
        )

    # 2. Hash the password using your passlib setup
    hashed_password = hash_password(user_in.password)

    # 3. Create the User (Defaulting to the Starter Plan)
    new_user = UserSchema(
        company_name=user_in.company_name,
        email=user_in.email,
        password_hash=hashed_password,
        phone=user_in.phone,
        role="user",
        current_plan_id=1, # Linking to the 'Starter' plan from your seed data
        is_active=True
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {
            "status": "success",
            "message": "Company account created",
            "company": new_user.company_name
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error during registration")
    




@app.get("/auth/google")
def login_google():
    """
    Step 1: Frontend links to /auth/google. 
    This redirects the user to Google's consent screen.
    """
    query_params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URL,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    url = f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(query_params)}"
    return RedirectResponse(url)


GOOGLE_AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_ENDPOINT = 'https://www.googleapis.com/oauth2/v2/userinfo'

if not all([GOOGLE_AUTH_ENDPOINT, GOOGLE_TOKEN_ENDPOINT, GOOGLE_USERINFO_ENDPOINT]):
    raise RuntimeError('missing required google oauth environment variables')

GOOGLE_CLIENT_ID= settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=settings.GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URL=settings.GOOGLE_REDIRECT_URL




@app.get("/auth/google/callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Step 2: Google redirects here with an authorization code.
    We exchange it for user data, register/login the user, 
    and pass control back to the frontend.
    """
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not found")

    # Exchange Authorization Code for Access Token
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URL,
        "grant_type": "authorization_code"
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(GOOGLE_TOKEN_ENDPOINT, data=data)
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        # Fetch User Profile from Google
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = await client.get(GOOGLE_USERINFO_ENDPOINT, headers=headers)
        user_info = user_info_response.json()

    email = user_info.get("email")
    name = user_info.get("name", "Google User")
    avatar_url = user_info.get("picture")
    google_id = user_info.get("id")

    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")

    # --- Database Operations ---
    # Check if user already exists
    user = db.query(UserSchema).filter(UserSchema.email == email).first()

    if not user:
        # If user doesn't exist, register them automatically
        try:
            user = UserSchema(
                company_name=name,  # Fallback to user's name as company name
                email=email,
                google_id = google_id,
                avatar_url = avatar_url,
                role="user",
                current_plan_id=1,  # Default starter plan
                is_active=True,
                auth_provider = "google"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error during Google registration")
        

