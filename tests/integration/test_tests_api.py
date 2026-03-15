import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, UTC

from app.schemas.tests.test import TestQuestions, QuestionStructure, QuestionType


class TestGetTestEndpoint:

    @pytest.mark.asyncio
    async def test_get_test_success(self, client, mock_db, fake_user):
        fake_test = MagicMock()
        fake_test.id = 1
        fake_test.title = "Test Quiz"
        fake_test.is_submitted = False
        fake_test.content = TestQuestions(
            questions=[
                QuestionStructure(
                    id=100,
                    question="What is Python?",
                    type=QuestionType(type_id=0, description="Short answer"),
                    required=True,
                )
            ]
        )
        fake_test.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        fake_test.user_id = fake_user.id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_test
        mock_db.execute.return_value = mock_result

        response = await client.get("/api/v1/tests/1")

        assert response.status_code == 200
        body = response.json()
        assert body["test_id"] == 1
        assert body["title"] == "Test Quiz"
        assert len(body["test_structure"]["questions"]) == 1

    @pytest.mark.asyncio
    async def test_get_test_not_found(self, client, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = await client.get("/api/v1/tests/999")

        assert response.status_code == 404


class TestSubmitStatusEndpoint:

    @pytest.mark.asyncio
    @patch("app.controllers.tests.TEST_RUNS_JOBS_STORAGE", {})
    async def test_status_not_found(self, client):
        response = await client.get("/api/v1/tests/submit-status/nonexistent-job")

        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch(
        "app.controllers.tests.TEST_RUNS_JOBS_STORAGE",
        {
            "job-abc": {
                "status": "processing",
                "processed_tests": 1,
                "total_tests": 3,
                "results": [],
            }
        },
    )
    async def test_status_processing(self, client):
        response = await client.get("/api/v1/tests/submit-status/job-abc")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "processing"
        assert body["processed_runs_count"] == 1
        assert body["total_runs"] == 3
