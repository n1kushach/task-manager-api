from collections.abc import Generator
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.core.config import settings
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"connect_timeout": 5},

)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
