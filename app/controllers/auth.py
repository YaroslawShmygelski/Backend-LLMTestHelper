import logging
from datetime import datetime, UTC

from fastapi import Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm.user import User
from app.schemas.token_response import TokenResponse
from app.utils.exception_types import NotFoundError, ForbiddenError, UnauthorizedError
from app.utils.jwt_tokens_handlers import (
    create_access_token,
    create_and_store_refresh_token,
    set_refresh_cookie,
    decode_token,
    get_db_refresh_token,
    get_cookies_refresh_token,
)
from app.services.users import verify_password

logger = logging.getLogger(__name__)


async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm,
    request: Request,
    response: Response,
    db_session: AsyncSession = None,
) -> TokenResponse:
    result = await db_session.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    logger.info("User is found", extra={"user_id": user.id})

    if user is None:
        raise NotFoundError("User Not Found")

    if not user.is_active:
        raise ForbiddenError("User is not active")

    if not verify_password(
        plain_password=form_data.password, hashed_password=user.password_hash
    ):
        raise UnauthorizedError("Incorrect username or password")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = await create_and_store_refresh_token(db_session, user.id, request)
    set_refresh_cookie(response, refresh_token)

    # Update User's last login in DB
    user.last_login = datetime.now(UTC)
    db_session.add(user)
    await db_session.commit()

    return TokenResponse(access_token=access_token, token_type="bearer")


async def refresh_access_token(
    request: Request, response: Response, db_session: AsyncSession
) -> TokenResponse:
    refresh_token = get_cookies_refresh_token(request)

    db_token = await get_db_refresh_token(db_session, refresh_token)

    db_token.revoked = True
    logger.info(
        "Old refresh token is revoked:",
        extra={"refresh_token_id": db_token.id, "user_id": db_token.user_id},
    )
    await db_session.commit()

    user_id = decode_token(refresh_token).get("sub")

    new_refresh_token = await create_and_store_refresh_token(
        db_session, user_id, request
    )
    new_access_token = create_access_token(data={"sub": str(user_id)})

    await db_session.commit()

    set_refresh_cookie(response, new_refresh_token)
    logger.info("New refresh token is created:", extra={"user_id": db_token.user_id})

    return TokenResponse(access_token=new_access_token, token_type="bearer")


async def logout_with_token(
    request: Request, response: Response, db_session: AsyncSession
):
    refresh_token = get_cookies_refresh_token(request)

    db_token = await get_db_refresh_token(db_session, refresh_token)

    db_token.revoked = True
    await db_session.commit()

    response.delete_cookie("refresh_token")

    logger.info("User logged out:", extra={"user_id": db_token.user_id})
