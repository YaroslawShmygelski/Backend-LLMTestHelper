"""This module contains api endpoints for the Users connected logics"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import users as user_controllers
from app.database.postgres_config import get_async_postgres_session
from app.schemas.User import UserCreate, UserResult

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.post("/register", response_model=UserResult)
async def register_user(
    payload: UserCreate,
    request: Request,
    db_session: AsyncSession = Depends(get_async_postgres_session),
):
    """User Registration endpoint"""
    result = await user_controllers.register_user(
        user_payload=payload, request=request, db_session=db_session
    )
    return result
