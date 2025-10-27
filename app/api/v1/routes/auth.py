"""This module contains api endpoints for the Authentication connected logics"""

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth import login_for_access_token
from app.database.postgres_config import get_async_postgres_session
from app.schemas.Token import Token

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/login", response_model=Token)
async def token(form_data: OAuth2PasswordRequestForm = Depends(),
                db_session: AsyncSession = Depends(get_async_postgres_session)):
    res = await login_for_access_token(form_data, db_session)
    return res
