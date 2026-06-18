from pydantic_settings import BaseSettings
from pydantic import field_validator
from urllib.parse import quote_plus
from typing import List, Optional, Union
import json


class Settings(BaseSettings):
    cors_origins: Union[List[str], str]
    cors_regex: Optional[str] = None

    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    LOG_LEVEL: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        if isinstance(v, str) and v.startswith("["):
             return json.loads(v)
        return v

    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_PORT: int = 3306

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URL: str

    TOKEN_SECRET_KEY: str
    ALGORITHM : str
    ACCESS_TOKEN_EXPIRE_MINUTES : int

    RESEND_API_KEY: str
    R2_ENDPOINT: str
    R2_BUCKET: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str

    FRONTEND_ACCOUNT_URL: str

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