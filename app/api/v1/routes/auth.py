"""This module contains api endpoints for the Authentication connected logics"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth import (
    login_for_access_token,
    refresh_access_token,
    logout_with_token,
)
from app.database.postgres_config import get_async_postgres_session
from app.models.orm.user import User
from app.schemas.token_response import TokenResponse
from app.services.users import get_user_from_token

auth_router = APIRouter(tags=["Authentication"])


@auth_router.post("/login", response_model=TokenResponse, status_code=200)
async def token(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db_session: Annotated[AsyncSession, Depends(get_async_postgres_session)],
):
    result = await login_for_access_token(
        form_data=form_data, request=request, response=response, db_session=db_session
    )
    return result


@auth_router.post("/refresh", response_model=TokenResponse, status_code=200)
async def refresh_token(
    request: Request,
    response: Response,
    db_session: Annotated[AsyncSession, Depends(get_async_postgres_session)],
):
    result = await refresh_access_token(
        request=request, response=response, db_session=db_session
    )
    return result


@auth_router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    current_user: Annotated[User, Depends(get_user_from_token)],
    db_session: Annotated[AsyncSession, Depends(get_async_postgres_session)],
):
    result = await logout_with_token(
        request=request, response=response, db_session=db_session
    )
    return result
