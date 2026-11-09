from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.security import oauth2_scheme
from app.core.database import get_db
from app.schemas.user import User, fake_users_db, UserInDB, fake_hash_password
from app.schemas.user import get_current_active_user

app = FastAPI()



@app.get("/items")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}

@app.get("/")
async def root():
    return {"message": "Hello World!"}

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"access_token": user.username, "token_type": "bearer"}
@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user

@app.get("/health/db")
async def check_database(db: Session = Depends(get_db)):
    print("1. Endpoint reached")

    try:
        print("2. Executing query")

        result = db.execute(text("SELECT 1"))

        print("3. Query executed")

        return {
            "status": "success",
            "database": "connected",
            "result": result.scalar(),
        }

    except Exception as e:
        print(f"Database error: {e}")

        raise HTTPException(
            status_code=503,
            detail=str(e),
        )