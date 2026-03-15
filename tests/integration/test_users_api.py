import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestRegisterEndpoint:

    @pytest.mark.asyncio
    @patch("app.services.users.get_password_hash", return_value="hashed_pw")
    async def test_register_success(self, mock_hash, client, mock_db, registration_payload):
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        async def fake_refresh(obj):
            obj.id = 42

        mock_db.refresh = AsyncMock(side_effect=fake_refresh)

        response = await client.post(
            "/api/v1/users/register",
            json=registration_payload,
        )

        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 42
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, mock_db, registration_payload):
        existing_user = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = existing_user

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        response = await client.post(
            "/api/v1/users/register",
            json=registration_payload,
        )

        assert response.status_code == 409
        assert response.json()["error"] == "CONFLICT"

    @pytest.mark.asyncio
    async def test_register_invalid_payload(self, client):
        response = await client.post(
            "/api/v1/users/register",
            json={"first_name": "Test"},
        )

        assert response.status_code == 422


class TestGetMeEndpoint:

    @pytest.mark.asyncio
    async def test_get_me_returns_current_user(self, client):
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "test@example.com"
        assert body["first_name"] == "Test"

    @pytest.mark.asyncio
    async def test_get_me_without_auth_returns_401(self):
        from app.main import app
        from httpx import AsyncClient, ASGITransport

        app.dependency_overrides.clear()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as raw_client:
            response = await raw_client.get("/api/v1/users/me")

        assert response.status_code == 401


class TestGetUserTestsEndpoint:

    @pytest.mark.asyncio
    async def test_get_user_tests_returns_list(self, client, mock_db):
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        response = await client.get("/api/v1/users/tests")

        assert response.status_code == 200
        body = response.json()
        assert body["offset"] == 0
        assert body["limit"] == 20
        assert body["tests"] == []
