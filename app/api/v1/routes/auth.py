"""This module contains api endpoints for the Authentication connected logics"""

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth import login_for_access_token, refresh_access_token
from app.database.postgres_config import get_async_postgres_session
from app.schemas.TokenResponse import TokenResponse

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/login", response_model=TokenResponse)
async def token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_session: AsyncSession = Depends(get_async_postgres_session),
):
    res = await login_for_access_token(
        form_data=form_data, request=request, response=response, db_session=db_session
    )
    return res


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db_session: AsyncSession = Depends(get_async_postgres_session),
):
    res = await refresh_access_token(
        request=request, response=response, db_session=db_session
    )
    return res
