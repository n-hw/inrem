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
