from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "InRem"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENV: str = "development"
    SECRET_KEY: str = "secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Encryption
    ENCRYPTION_KEY: str | None = None  # Fernet key for field-level encryption
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str | None = None  # Path to service account JSON

    # Observability
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: str | None = None  # Optional: errors → Sentry when set

    # CORS — comma-separated list of allowed origins.
    # Empty / unset 이면 RN dev 환경(localhost·LAN IP) 만 허용 (개발 안전).
    # 프로덕션 출시 시 "https://app.inrem.io" 같은 실제 도메인으로 좁힐 것.
    CORS_ALLOW_ORIGINS: str = ""

    # Email (Gmail SMTP — dev/alpha). 비워두면 MockEmailProvider 로 폴백.
    # 사용자 셋업: Google 계정 → 보안 → 2FA → "앱 비밀번호" 생성 후 입력.
    GMAIL_USERNAME: str | None = None
    GMAIL_APP_PASSWORD: str | None = None
    GMAIL_FROM_NAME: str | None = None  # 발신자 표시 이름, 기본 "InRem"

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = "../.env"
        case_sensitive = True

settings = Settings()
