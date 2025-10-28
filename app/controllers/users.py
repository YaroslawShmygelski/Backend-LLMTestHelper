from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm.user import User
from app.schemas.user import UserCreate, UserResult
from app.services.user_auth import get_password_hash


async def register_user(
    user_payload: UserCreate, request: Request, db_session: AsyncSession = None
) -> UserResult:
    res = await db_session.execute(select(User).where(User.email == user_payload.email))
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    res = await db_session.execute(
        select(User).where(
            User.country_code == user_payload.country_code,
            User.phone_number == user_payload.phone_number,
        )
    )
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Phone number already registered")

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
        return UserResult.model_validate(user)
    except IntegrityError as e:
        raise HTTPException(
            status_code=400, detail=f"Database integrity error: {str(e.orig)}"
        ) from e
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}") from e
