from typing import Annotated
from fastapi import APIRouter, Depends

from app.schemas.user import UserBase
# from app.services.auth_service import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])


# @router.get("/me")
# async def read_users_me(current_user: Annotated[UserBase, Depends(get_current_active_user)]) -> UserBase:
#     return current_user


# @router.get("/me/items")
# async def read_own_items(current_user: UserBase = Depends(get_current_active_user)):
#     return [{"item_id": "Foo", "owner": current_user.username}]
