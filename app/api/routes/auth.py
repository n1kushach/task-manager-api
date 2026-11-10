from typing import Annotated
from fastapi import status
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import EmailAlreadyRegistered, authenticate_user, register_user
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, responses={
    409: {"description": "Email already registered"},
})
def register(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)]
):
    try:
        return register_user(db, payload.email, payload.password)
    except EmailAlreadyRegistered:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Email already registered")


@router.post("/login", response_model=Token, responses={401: {"description": "Incorrect email or password"}})
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return Token(access_token=create_access_token(user.id))
