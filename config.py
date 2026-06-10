from pydantic_settings import BaseSettings
from urllib.parse import quote_plus


class Settings(BaseSettings):
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_PORT: int = 3306

    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URL: str

    # TOKEN SECRET_KEY
    TOKEN_SECRET_KEY: str

    RESEND_API_KEY: str
    R2_ENDPOINT: str
    R2_BUCKET: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str

    FRONTEND_ACCOUNT_URL: str = "http://127.0.0.1:3000/Signin.html"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def database_url(self):
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+pymysql://{self.DB_USER}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()