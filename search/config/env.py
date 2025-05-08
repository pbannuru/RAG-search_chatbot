from enum import Enum
import time
from pydantic_settings import BaseSettings


class EnvironmentFilesEnum(Enum):
    LOCAL = ".env.local"
    DEVELOPMENT = ".env.server.dev"
    STAGING = ".env.server.staging"
    PRODUCTION = ".env.server.prod"


class Serverenv(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentVars(BaseSettings):
    DEBUG_MODE: bool = False
    DATABASE_DRIVER: str = "mysql+pymysql"
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_USERNAME: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    DATABASE_SYNC: bool
    DATABASE_LOGGING: bool
    DATABASE_USE_CERT: bool
    DATABASE_POOL_PRE_PING: bool = True
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_POOL_ECHO: bool = True
    DATABASE_POOL_USE_LIFO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_POOL_MAX_OVERFLOW_LIMIT: int = 10
    SERVER_ENV: Serverenv = Serverenv.DEVELOPMENT
    AUTH_KAAS_CLIENT_SECRET: str
    AUTH_KZ_CLIENT_SECRET: str
    AUTH_APP_CLIENT_SECRET: str
    AUTH_DOCCEBO_PASSWORD: str
    AUTH_OPENSEARCH_PASSWORD: str
    KZ_USE_PROXY: bool = False

    PROFILING_ENABLED: bool = True
    PROGRAM_START_TIME: float = time.time()

    class Config:
        env_file = EnvironmentFilesEnum.DEVELOPMENT.value


environment = EnvironmentVars()
