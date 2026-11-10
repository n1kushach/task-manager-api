from typing import Annotated, Generator
from app.core.security import oauth2_scheme
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User | None:
    user_id = decode_access_token(token)
    user = db.get(User, user_id) if user_id is not None else None
    if not user or not user.is_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user
