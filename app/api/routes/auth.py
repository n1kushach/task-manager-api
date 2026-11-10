from datetime import timedelta
from typing import Annotated
from fastapi import status
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.core.config import settings
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import EmailAlreadyRegistered, authenticate_user, register_user
from sqlalchemy.orm import Session
from app.core.database import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


# @router.post("/token")
# async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
#     user = authenticate_user(
#         fake_users_db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"}
#         )
#     access_token_expires = timedelta(
#         minutes=settings.access_token_expire_minutes)
#     access_token = create_access_token(
#         data={"sub": user.username}, expires_delta=access_token_expires)
#     return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, responses={
    409: {"description": "Email already registered"},
    422: {"description": "Validation error"}
})
async def register(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)]
):
    try:
        return register_user(db, payload.email, payload.password)
    except EmailAlreadyRegistered:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Email already registered")
