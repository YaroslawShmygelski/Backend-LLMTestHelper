import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.controllers.auth import login_for_access_token
from app.utils.exception_types import NotFoundError, ForbiddenError, UnauthorizedError


@pytest.fixture
def mock_form_data():
    form = MagicMock()
    form.username = "test@example.com"
    form.password = "CorrectPassword"
    return form


@pytest.fixture
def mock_request():
    return MagicMock()


@pytest.fixture
def mock_response():
    return MagicMock()


class TestLoginForAccessToken:

    @pytest.mark.asyncio
    @patch("app.controllers.auth.set_refresh_cookie")
    @patch("app.controllers.auth.create_and_store_refresh_token")
    @patch("app.controllers.auth.create_access_token")
    @patch("app.controllers.auth.verify_password")
    async def test_login_success(
        self,
        mock_verify,
        mock_create_access,
        mock_create_refresh,
        mock_set_cookie,
        fake_user,
        mock_db,
        mock_form_data,
        mock_request,
        mock_response,
    ):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_user
        mock_db.execute.return_value = mock_result

        mock_verify.return_value = True
        mock_create_access.return_value = "test_access_token"
        mock_create_refresh.return_value = "test_refresh_token"

        result = await login_for_access_token(
            form_data=mock_form_data,
            request=mock_request,
            response=mock_response,
            db_session=mock_db,
        )

        assert result.access_token == "test_access_token"
        assert result.token_type == "bearer"
        mock_set_cookie.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_user_not_found(
        self, mock_db, mock_form_data, mock_request, mock_response
    ):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundError):
            await login_for_access_token(
                form_data=mock_form_data,
                request=mock_request,
                response=mock_response,
                db_session=mock_db,
            )

    @pytest.mark.asyncio
    async def test_login_user_inactive(
        self, fake_user, mock_db, mock_form_data, mock_request, mock_response
    ):
        fake_user.is_active = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_user
        mock_db.execute.return_value = mock_result

        with pytest.raises(ForbiddenError):
            await login_for_access_token(
                form_data=mock_form_data,
                request=mock_request,
                response=mock_response,
                db_session=mock_db,
            )

    @pytest.mark.asyncio
    @patch("app.controllers.auth.verify_password", return_value=False)
    async def test_login_wrong_password(
        self,
        mock_verify,
        fake_user,
        mock_db,
        mock_form_data,
        mock_request,
        mock_response,
    ):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_user
        mock_db.execute.return_value = mock_result

        with pytest.raises(UnauthorizedError):
            await login_for_access_token(
                form_data=mock_form_data,
                request=mock_request,
                response=mock_response,
                db_session=mock_db,
            )
