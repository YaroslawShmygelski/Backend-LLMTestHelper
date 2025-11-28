import os
from datetime import timedelta, datetime, UTC
from hashlib import sha256
from typing import Any

from jose import jwt
from dotenv import load_dotenv
from fastapi import Request, Response
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.orm.refresh_token import RefreshToken
from app.utils.exception_types import UnauthorizedError

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("AUTH_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")


def create_access_token(data: dict) -> str:
    """Creation on JWT Access token"""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> (str, datetime):
    """Creation refresh token"""
    to_encode = data.copy()
    expires_at = datetime.now(UTC) + timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS))

    # JWT expects exp as UNIX timestamp
    to_encode.update({"exp": int(expires_at.timestamp()), "type": "refresh"})

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token, expires_at


async def create_and_store_refresh_token(
    db_session: AsyncSession, user_id: int, request: Request
) -> str:

    await revoke_user_tokens(db_session, user_id)

    refresh_token, expires_at = create_refresh_token(data={"sub": str(user_id)})
    token_hash = hash_refresh_token(refresh_token)

    ip_address = request.headers.get("x-real-ip") or request.client.host

    db_session.add(
        RefreshToken(
            user_id=int(user_id),
            token_hash=token_hash,
            user_agent=request.headers.get("User-Agent"),
            ip_address=ip_address,
            expires_at=expires_at,
            revoked=False,
        )
    )
    return refresh_token


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=int(timedelta(days=float(REFRESH_TOKEN_EXPIRE_DAYS)).total_seconds()),
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie("refresh_token")


def decode_token(token: str) -> dict[str, Any]:
    """Decode JWT token"""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload


def hash_refresh_token(refresh_token: str) -> str:
    data = refresh_token.encode("utf-8")
    return sha256(data).hexdigest()


async def revoke_user_tokens(db_session: AsyncSession, user_id: int) -> None:
    await db_session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == int(user_id), RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )


def get_cookies_refresh_token(request: Request) -> str:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise UnauthorizedError(message="Incorrect refresh token")
    return refresh_token


async def get_db_refresh_token(
    db_session: AsyncSession, refresh_token: str
) -> RefreshToken:

    token_hash = hash_refresh_token(refresh_token)
    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.revoked:
        raise UnauthorizedError(message="Refresh token is wrong or revoked")
    if not db_token.expires_at < datetime.now(UTC):
        raise UnauthorizedError(message="Refresh token expired")

    return db_token
