import logging

from fastapi import HTTPException, Request, Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm.user import User
from app.schemas.users import UserCreate, UserResult, UserBase
from app.services.users import get_password_hash, get_user_from_token
from app.utils.exception_types import ConflictError
from app.utils.logging import correlation_id

logger = logging.getLogger(__name__)


async def register_user(
    user_payload: UserCreate, request: Request, db_session: AsyncSession = None
) -> UserResult:
    res = await db_session.execute(select(User).where(User.email == user_payload.email))
    if res.scalars().first():
        raise ConflictError(message="Email already registered")

    res = await db_session.execute(
        select(User).where(
            User.country_code == user_payload.country_code,
            User.phone_number == user_payload.phone_number,
        )
    )
    if res.scalars().first():
        raise ConflictError(message="Phone number already registered")

    real_ip = request.headers.get("x-real-ip")
    forward_for = request.headers.get("x-forwarded-for")
    client_host = request.client.host
    ip_address = real_ip if real_ip else forward_for if forward_for else client_host

    hashed_password = get_password_hash(user_payload.password)

    try:
        user = User(
            email=str(user_payload.email),
            first_name=user_payload.first_name,
            last_name=user_payload.last_name,
            phone_number=user_payload.phone_number,
            country_code=user_payload.country_code,
            is_premium=False,
            ip_address=ip_address,
            password_hash=hashed_password,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        logger.info(
            "user_created",
            extra={
                "user_id": user.id,
                "email": user.email,
                "mobile_number": user.phone_number,
                "ip": user.ip_address,
                "correlation_id": correlation_id.get(),
            },
        )
        return UserResult.model_validate(user)
    except IntegrityError as e:
        raise HTTPException(
            status_code=400, detail=f"Database integrity error: {str(e.orig)}"
        ) from e
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}") from e


async def get_current_user_from_db(
    current_user: User = Depends(get_user_from_token),
) -> UserBase:
    return UserBase.model_validate(current_user)
