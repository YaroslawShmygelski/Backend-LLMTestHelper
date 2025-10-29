"""This module contains api endpoints for the Users connected logics"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import users as user_controllers
from app.controllers.users import get_current_user_from_db
from app.database.postgres_config import get_async_postgres_session
from app.schemas.users import UserCreate, UserResult, UserBase

user_router = APIRouter(tags=["Users"])


@user_router.post("/register", response_model=UserResult)
async def register_user(
    payload: UserCreate,
    request: Request,
    db_session: Annotated[AsyncSession, Depends(get_async_postgres_session)],
):
    """User Registration endpoint"""
    result = await user_controllers.register_user(
        user_payload=payload, request=request, db_session=db_session
    )
    return result


@user_router.get("/me", response_model=UserBase)
async def get_current_user(
    current_user: UserBase = Depends(user_controllers.get_current_user_from_db),
):
    return current_user
