import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.users import get_user_from_token
from app.database.postgres_config import get_async_postgres_session
from app.database.models.orm.user import User
from app.settings import TEST_RUNS_JOBS_STORAGE
from app.utils.enums import JobStatus


def _fake_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.phone_number = 123456789
    user.country_code = 48
    user.is_active = True
    user.is_premium = False
    return user

def _fake_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def override_deps():
    fake_user = _fake_user()
    fake_session = _fake_session()

    app.dependency_overrides[get_user_from_token] = lambda: fake_user
    app.dependency_overrides[get_async_postgres_session] = lambda: fake_session

    yield fake_user, fake_session

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestSubmitStatusEndpoint:

    @pytest.mark.asyncio
    async def test_submit_status_not_found(self, client, override_deps):
        response = await client.get("/api/v1/tests/submit-status/nonexistent-id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_submit_status_processing(self, client, override_deps):
        TEST_RUNS_JOBS_STORAGE["ep-job-1"] = {
            "status": JobStatus.PROCESSING,
            "total_tests": 3,
            "processed_tests": 1,
            "results": [],
        }
        response = await client.get("/api/v1/tests/submit-status/ep-job-1")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["processed_runs_count"] == 1
        assert data["total_runs"] == 3

    @pytest.mark.asyncio
    async def test_submit_status_completed(self, client, override_deps):
        TEST_RUNS_JOBS_STORAGE["ep-job-2"] = {
            "status": JobStatus.COMPLETED,
            "total_tests": 1,
            "processed_tests": 1,
            "results": [{"run_id": 5, "status": "completed"}],
        }
        response = await client.get("/api/v1/tests/submit-status/ep-job-2")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert len(data["results"]) == 1


class TestSubmitTestEndpoint:

    @pytest.mark.asyncio
    async def test_submit_returns_202(self, client, override_deps):
        response = await client.post(
            "/api/v1/tests/submit/42",
            json={"quantity": 1, "answers": [{"question_id": 100, "answer_mode": "llm"}]},
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_submit_creates_job_in_storage(self, client, override_deps):
        response = await client.post(
            "/api/v1/tests/submit/42",
            json={"quantity": 3, "answers": []},
        )
        job_id = response.json()["job_id"]
        assert job_id in TEST_RUNS_JOBS_STORAGE
        assert TEST_RUNS_JOBS_STORAGE[job_id]["total_tests"] == 3


class TestGetTestEndpoint:

    @pytest.mark.asyncio
    async def test_get_test_calls_controller(self, client, override_deps):
        _, fake_session = override_deps
        res_mock = MagicMock()
        res_mock.scalar_one_or_none.return_value = None
        fake_session.execute.return_value = res_mock

        response = await client.get("/api/v1/tests/1")
        assert response.status_code in (200, 404)


class TestUserEndpoints:

    @pytest.mark.asyncio
    async def test_register_validation_error(self, client, override_deps):
        response = await client.post("/api/v1/users/register", json={"email": "bad"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client, override_deps):
        response = await client.post("/api/v1/users/register", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_me(self, client, override_deps):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"


class TestAuthEndpoints:

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client, override_deps):
        response = await client.post("/api/v1/auth/login", data={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_refresh_no_cookie(self, client, override_deps):
        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == 401
