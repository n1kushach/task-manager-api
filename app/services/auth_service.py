from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Annotated
from app.core.security import hash_password
from alembic.util import status
from app.core.security import oauth2_scheme
from fastapi import Depends, HTTPException
from app.core.config import settings
import jwt
from pwdlib import PasswordHash
from app.models.user import User
from app.schemas.token import TokenData
from app.schemas.user import UserBase, UserInDB

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": hash_password("secret"),
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": hash_password("secret2"),
        "disabled": True,
    },
}


class EmailAlreadyRegistered(Exception):
    pass


password_hash = PasswordHash.recommended()
DUMMY_hash = password_hash.hash("dummypassword")


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email)).first()


def register_user(db: Session, email: str, password: str) -> User:
    if get_user_by_email(db, email):
        raise EmailAlreadyRegistered
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key,
                             algorithms=[settings.algorithm])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    # Added
    if token_data.username is None:
        raise credentials_exception
    # Added
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# async def get_current_active_user(current_user: Annotated[UserBase, Depends(get_current_user)]):
#     if current_user.disabled:
#         raise HTTPException(
#             status_code=400,
#             detail="Inactive user"
#         )
#     return current_user
