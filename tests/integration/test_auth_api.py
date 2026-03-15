import pytest
from unittest.mock import MagicMock, patch


class TestLoginEndpoint:

    @pytest.mark.asyncio
    @patch("app.controllers.auth.set_refresh_cookie")
    @patch("app.controllers.auth.create_and_store_refresh_token", return_value="refresh_tok")
    @patch("app.controllers.auth.create_access_token", return_value="access_tok")
    @patch("app.controllers.auth.verify_password", return_value=True)
    async def test_login_returns_200_with_token(
        self, mock_verify, mock_access, mock_refresh, mock_cookie,
        client, fake_user, mock_db,
    ):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_user
        mock_db.execute.return_value = mock_result

        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "Correct"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] == "access_tok"
        assert body["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_returns_404_when_user_not_found(self, client, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@test.com", "password": "whatever"},
        )

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "NOT_FOUND"

    @pytest.mark.asyncio
    @patch("app.controllers.auth.verify_password", return_value=False)
    async def test_login_returns_401_on_wrong_password(
        self, mock_verify, client, fake_user, mock_db
    ):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_user
        mock_db.execute.return_value = mock_result

        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "wrong"},
        )

        assert response.status_code == 401
