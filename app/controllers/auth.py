from datetime import datetime, UTC

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ORM.User import User
from app.schemas.Token import Token
from app.services.jwt_tokens_handlers import create_access_token
from app.services.user_auth import verify_password


async def login_for_access_token(form_data: OAuth2PasswordRequestForm,
                                 db_session: AsyncSession = None) -> Token:
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

    if not verify_password(plain_password=form_data.password, hashed_password=user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    # Update User's last login in DB
    user.last_login = datetime.now(UTC)
    db_session.add(user)
    await db_session.commit()

    return Token(token=access_token, token_type="bearer")
