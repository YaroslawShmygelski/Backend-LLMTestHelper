import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.database.models.orm.user import User
from app.database.postgres_config import get_async_postgres_session
from app.services.users import get_user_from_token


@pytest.fixture
def fake_user() -> MagicMock:
    user = MagicMock(spec=User)
    user.id = 1
    user.first_name = "Test"
    user.last_name = "User"
    user.email = "test@example.com"
    user.phone_number = 123456789
    user.country_code = 48
    user.is_premium = False
    user.is_active = True
    user.is_verified = False
    user.password_hash = "hashed_password"
    user.ip_address = "127.0.0.1"
    user.last_login = None
    return user


@pytest.fixture
def mock_db() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def registration_payload() -> dict:
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": "newuser@example.com",
        "country_code": 48,
        "phone_number": 987654321,
        "password": "SecurePass123",
    }


@pytest_asyncio.fixture
async def client(fake_user, mock_db):
    from app.main import app

    async def override_db():
        yield mock_db

    async def override_user():
        return fake_user

    app.dependency_overrides[get_async_postgres_session] = override_db
    app.dependency_overrides[get_user_from_token] = override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
