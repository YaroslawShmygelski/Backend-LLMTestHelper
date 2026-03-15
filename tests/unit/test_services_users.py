import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.users import verify_password, get_password_hash, get_user_from_token
from app.utils.exception_types import UnauthorizedError, NotFoundError


class TestPasswordHashing:

    def test_hash_is_not_plaintext(self):
        password = "SuperSecret123"
        hashed = get_password_hash(password)
        assert hashed != password

    def test_correct_password_verifies(self):
        password = "MyPassword!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password_does_not_verify(self):
        hashed = get_password_hash("RealPassword")
        assert verify_password("WrongPassword", hashed) is False

    def test_different_passwords_produce_different_hashes(self):
        hash1 = get_password_hash("PasswordOne")
        hash2 = get_password_hash("PasswordTwo")
        assert hash1 != hash2


class TestGetUserFromToken:

    @pytest.mark.asyncio
    @patch("app.services.users.decode_token")
    async def test_returns_user_when_token_valid(self, mock_decode, fake_user, mock_db):
        mock_decode.return_value = {"sub": "1"}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_user
        mock_db.execute.return_value = mock_result

        user = await get_user_from_token(db_session=mock_db, token="valid.jwt.token")

        assert user.id == 1
        assert user.email == "test@example.com"
        mock_decode.assert_called_once_with("valid.jwt.token")

    @pytest.mark.asyncio
    @patch("app.services.users.decode_token")
    async def test_raises_unauthorized_on_invalid_jwt(self, mock_decode, mock_db):
        from jose import JWTError

        mock_decode.side_effect = JWTError("bad token")

        with pytest.raises(UnauthorizedError):
            await get_user_from_token(db_session=mock_db, token="invalid.token")

    @pytest.mark.asyncio
    @patch("app.services.users.decode_token")
    async def test_raises_not_found_when_user_missing(self, mock_decode, mock_db):
        mock_decode.return_value = {"sub": "999"}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundError):
            await get_user_from_token(db_session=mock_db, token="valid.but.orphan")
