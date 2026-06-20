from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.rate_limiter import limiter
from api.v1.auth.register import router as register_router
from api.v1.auth.google_auth import router as google_router
from api.v1.auth.login import router as login_router 
from api.v1.auth.email_auth import router as email_router
from api.v1.plan import router as plans_router

from api.v1.users import router as users_router
from api.v1.reviews import router as reviews_router
from api.v1.requests import router as file_router

from api.v1.admin.users import router as admin_users_router
from api.v1.admin.reviews import router as admin_reviews_router
from api.v1.admin.requests import router as admin_requests_router
from api.v1.admin.plans import router as admin_plans_router
from api.v1.admin.storage import router as admin_storage_router
from api.v1.admin.payments import router as admin_notifications_router
from api.v1.admin.dashboard import router as admin_dashboard_router

from config import settings
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration







IS_PROD = settings.ENV == "production"

app = FastAPI(
    title="BADIA API",
    description="Official API for the BADIA platform.",
    version="1.0.0",
    contact={
        "name": "BADIA Support",
        "email": "support@badiaprojectmanagement.com",
    },
    license_info={
        "name": "Proprietary",
    },

    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
)


sentry_dsn = settings.SENTRY_DSN

if sentry_dsn and settings.ENV == "production":
    sentry_sdk.init(
        dsn=sentry_dsn,
        send_default_pii=False,
        integrations=[
            FastApiIntegration(),
        ],
    )





# SlowAPI rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)




@app.get("/")
async def root():
    return {"status": "active", "message": "BADIA API is running"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


middleware_kwargs = dict(
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.cors_regex:
    middleware_kwargs["allow_origin_regex"] = settings.cors_regex

app.add_middleware(CORSMiddleware, **middleware_kwargs)


app.include_router(register_router, prefix="/api/v1")
app.include_router(login_router, prefix="/api/v1")
app.include_router(google_router, prefix="/api/v1/auth")
app.include_router(users_router, prefix="/api/v1/users")
app.include_router(reviews_router, prefix="/api/v1/reviews")
app.include_router(email_router, prefix="/api/v1")
app.include_router(plans_router, prefix="/api/v1/plans")
app.include_router(file_router, prefix="/api/v1/files")

# Admin routers (modular)
app.include_router(admin_dashboard_router, prefix="/api/v1/admin")
app.include_router(admin_users_router, prefix="/api/v1/admin")
app.include_router(admin_reviews_router, prefix="/api/v1/admin")
app.include_router(admin_requests_router, prefix="/api/v1/admin")
app.include_router(admin_plans_router, prefix="/api/v1/admin")
app.include_router(admin_storage_router, prefix="/api/v1/admin")
app.include_router(admin_notifications_router, prefix="/api/v1/admin")
