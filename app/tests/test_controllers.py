"""Tests for app/controllers/tests.py — test controller logic."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.controllers.tests import (
    start_test_batch,
    get_run_status,
)
from app.schemas.tests.test import (
    TestSubmitPayload,
    Answer,
    SubmitTestResponse,
    RunJobStatusResponse,
)
from app.settings import TEST_RUNS_JOBS_STORAGE
from app.utils.enums import JobStatus
from app.utils.exception_types import NotFoundError


class TestStartTestBatch:

    @pytest.mark.asyncio
    async def test_returns_submit_response(self, mock_user):
        payload = TestSubmitPayload(
            quantity=3,
            answers=[Answer(question_id=100, answer_mode="llm")],
        )
        bg_tasks = MagicMock()

        result = await start_test_batch(
            test_id=42, payload=payload,
            current_user=mock_user, background_tasks=bg_tasks,
        )
        assert isinstance(result, SubmitTestResponse)
        assert result.job_id is not None
        assert "job_id" in result.message or "Poll" in result.message

    @pytest.mark.asyncio
    async def test_registers_background_task(self, mock_user):
        payload = TestSubmitPayload(quantity=1, answers=[])
        bg_tasks = MagicMock()

        await start_test_batch(
            test_id=42, payload=payload,
            current_user=mock_user, background_tasks=bg_tasks,
        )
        bg_tasks.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_initializes_job_storage(self, mock_user):
        payload = TestSubmitPayload(quantity=5, answers=[])
        bg_tasks = MagicMock()

        result = await start_test_batch(
            test_id=42, payload=payload,
            current_user=mock_user, background_tasks=bg_tasks,
        )

        job = TEST_RUNS_JOBS_STORAGE[result.job_id]
        assert job["status"] == JobStatus.PENDING
        assert job["total_tests"] == 5
        assert job["processed_tests"] == 0
        assert job["results"] == []


class TestGetRunStatus:

    @pytest.mark.asyncio
    async def test_raises_not_found_for_unknown_job(self):
        with pytest.raises(NotFoundError):
            await get_run_status("nonexistent-job-id")

    @pytest.mark.asyncio
    async def test_returns_processing_status(self):
        TEST_RUNS_JOBS_STORAGE["test-job-1"] = {
            "status": JobStatus.PROCESSING,
            "total_tests": 3,
            "processed_tests": 1,
            "results": [],
        }

        result = await get_run_status("test-job-1")
        assert isinstance(result, RunJobStatusResponse)
        assert result.status == JobStatus.PROCESSING
        assert result.processed_runs_count == 1
        assert result.total_runs == 3
        assert result.results is None

    @pytest.mark.asyncio
    async def test_returns_completed_with_results(self):
        TEST_RUNS_JOBS_STORAGE["test-job-2"] = {
            "status": JobStatus.COMPLETED,
            "total_tests": 1,
            "processed_tests": 1,
            "results": [{"run_id": 10, "status": "completed"}],
        }

        result = await get_run_status("test-job-2")
        assert result.status == JobStatus.COMPLETED
        assert result.results is not None
        assert len(result.results) == 1
