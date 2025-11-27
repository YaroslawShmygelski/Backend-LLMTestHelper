"""This module contains api endpoints for the Users connected logics"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import users as user_controllers
from app.database.postgres_config import get_async_postgres_session
from app.models.orm.user import User
from app.schemas.users import (
    UserCreate,
    UserResult,
    UserBase,
    UserTests,
    UserTestsResponse,
)
from app.services.users import get_user_from_token

user_router = APIRouter(tags=["Users"])


@user_router.post("/register", response_model=UserResult, status_code=201)
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


@user_router.get("/me", response_model=UserBase, status_code=200)
async def get_current_user(
    current_user: UserBase = Depends(user_controllers.get_current_user_from_db),
):
    return current_user


@user_router.get("/tests", response_model=UserTestsResponse, status_code=200)
async def get_user_tests(
    db_session: Annotated[AsyncSession, Depends(get_async_postgres_session)],
    current_user: User = Depends(get_user_from_token),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, description="Limit for pagination"),
) -> UserTestsResponse:
    result = await user_controllers.get_user_tests(
        current_user=current_user,
        async_db_session=db_session,
        offset=offset,
        limit=limit,
    )
    return result
