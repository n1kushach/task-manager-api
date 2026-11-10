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
