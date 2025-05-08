from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.env import environment

SQLALCHEMY_DATABASE_URL = f"{environment.DATABASE_DRIVER}://{environment.DATABASE_USERNAME}:{environment.DATABASE_PASSWORD}@{environment.DATABASE_HOST}:{environment.DATABASE_PORT}/{environment.DATABASE_NAME}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=environment.DATABASE_LOGGING,
    pool_pre_ping=environment.DATABASE_POOL_PRE_PING,
    pool_recycle=environment.DATABASE_POOL_RECYCLE,
    echo_pool="debug" if environment.DATABASE_POOL_ECHO is True else None,
    pool_use_lifo=environment.DATABASE_POOL_USE_LIFO,
    pool_size=environment.DATABASE_POOL_SIZE,
    max_overflow=environment.DATABASE_POOL_MAX_OVERFLOW_LIMIT,
    # connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        print("Yield DB connection")
        yield db
    except Exception as e:
        print("Errored DB connection")
        db.rollback()
        raise e
    finally:
        print("Closing DB connection")
        db.close()


class DbDepends:
    def __init__(self):
        print("DbDepends Requesting DB Connection")
        try:
            self.db = SessionLocal()
        except:
            print("DbDepends Errored DB")
            self.db.rollback()

    def __enter__(self):
        return self.db

    def __exit__(self, *args):
        print("DbDepends Closing Connection")
        self.db.close()
