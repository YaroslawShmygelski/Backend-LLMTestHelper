from datetime import datetime, UTC

from fastapi import HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm.refresh_token import RefreshToken
from app.models.orm.user import User
from app.schemas.token_response import TokenResponse
from app.services.jwt_tokens_handlers import (
    create_access_token,
    create_and_store_refresh_token,
    set_refresh_cookie,
    hash_refresh_token,
    decode_token,
)
from app.services.users import verify_password


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

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Inactive user",
        )

    if not verify_password(
        plain_password=form_data.password, hashed_password=user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Incorrect refresh token")

    token_hash = hash_refresh_token(refresh_token)
    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()
    print(refresh_token)
    print(db_token)

    if not db_token or db_token.revoked or db_token.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    db_token.revoked = True
    await db_session.commit()

    user_id = decode_token(refresh_token).get("sub")
    print(user_id)

    new_refresh_token = await create_and_store_refresh_token(
        db_session, user_id, request
    )
    print(new_refresh_token)
    new_access_token = create_access_token(data={"sub": str(user_id)})

    await db_session.commit()

    set_refresh_cookie(response, new_refresh_token)

    return TokenResponse(access_token=new_access_token, token_type="bearer")
