"""Tests for app/controllers/auth.py — authentication controller."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.controllers.auth import login_for_access_token
from app.utils.exception_types import NotFoundError, ForbiddenError, UnauthorizedError


class TestLoginForAccessToken:

    def _make_form_data(self, username="test@example.com", password="test1234"):
        form = MagicMock()
        form.username = username
        form.password = password
        return form

    def _make_request(self):
        request = MagicMock()
        request.headers = {"x-real-ip": "127.0.0.1", "User-Agent": "test"}
        request.client.host = "127.0.0.1"
        return request

    @pytest.mark.asyncio
    async def test_user_not_found_raises(self, mock_db_session):
        # Mock: no user found
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = result_mock

        form_data = self._make_form_data()
        request = self._make_request()
        response = MagicMock()

        with pytest.raises(NotFoundError):
            await login_for_access_token(
                form_data=form_data,
                request=request,
                response=response,
                db_session=mock_db_session,
            )

    @pytest.mark.asyncio
    async def test_inactive_user_raises(self, mock_db_session, mock_user):
        mock_user.is_active = False
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = result_mock

        form_data = self._make_form_data()
        request = self._make_request()
        response = MagicMock()

        with pytest.raises(ForbiddenError):
            await login_for_access_token(
                form_data=form_data,
                request=request,
                response=response,
                db_session=mock_db_session,
            )

    @pytest.mark.asyncio
    @patch("app.controllers.auth.verify_password", return_value=False)
    async def test_wrong_password_raises(self, mock_verify, mock_db_session, mock_user):
        mock_user.is_active = True
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = result_mock

        form_data = self._make_form_data()
        request = self._make_request()
        response = MagicMock()

        with pytest.raises(UnauthorizedError):
            await login_for_access_token(
                form_data=form_data,
                request=request,
                response=response,
                db_session=mock_db_session,
            )
