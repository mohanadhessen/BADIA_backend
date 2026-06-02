from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.auth.register import router as register_router
from api.v1.auth.google_auth import router as google_router
from api.v1.auth.login import router as login_router 
from api.v1.auth.email_service import router as email_router
from api.v1.plan import router as plans_router
from api.v1.auth.admin import router as admin_router

from api.v1.users import router as users_router
from api.v1.reviews import router as reviews_router
from api.v1.submit_request import router as file_router


app = FastAPI(title="BADIA API")

origins = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://badia-frontend.mohanadhessen.workers.dev/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Auth routes
app.include_router(register_router, prefix="/api/v1")
app.include_router(login_router, prefix="/api/v1")
app.include_router(google_router, prefix="/auth")
app.include_router(users_router, prefix="/api/v1/users")
app.include_router(reviews_router, prefix="/api/v1/reviews")
app.include_router(email_router, prefix="/api/v1/email")
app.include_router(plans_router,prefix="/api/v1/plans")
app.include_router(admin_router,prefix="/api/v1/admin")
app.include_router(file_router,prefix="/api/v1/files")

