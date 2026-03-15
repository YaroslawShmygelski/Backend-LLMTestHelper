import pytest
from unittest.mock import patch, MagicMock

from app.services.tests.tests import (
    normalize_parsed_data,
    fill_random_value,
    build_google_form_payload,
)
from app.controllers.tests import get_run_status
from app.schemas.tests.test import AnsweredQuestionStructure, QuestionType
from app.utils.exception_types import NotFoundError
from app.utils.enums import JobStatus


class TestNormalizeParsedData:

    @patch("app.services.tests.tests.get_form_type_description")
    def test_normalizes_valid_questions(self, mock_get_type):
        mock_get_type.return_value = QuestionType(type_id=2, description="Multiple choice")

        raw_data = [
            {
                "id": 100,
                "type": 2,
                "container_name": "What is your favorite color?",
                "required": True,
                "options": ["Red", "Blue", "Green"],
            },
            {
                "id": 200,
                "type": 0,
                "name": "Your name",
                "required": False,
                "options": None,
            },
        ]

        result = normalize_parsed_data(raw_data)

        assert len(result.questions) == 2
        assert result.questions[0].id == 100
        assert result.questions[0].question == "What is your favorite color?"
        assert result.questions[0].required is True
        assert result.questions[1].id == 200

    @patch("app.services.tests.tests.get_form_type_description")
    def test_skips_non_integer_type(self, mock_get_type):
        raw_data = [
            {"id": 1, "type": "section_header", "name": "Section 1"},
            {"id": 2, "type": 0, "name": "Question", "required": True, "options": None},
        ]

        mock_get_type.return_value = QuestionType(type_id=0, description="Short answer")

        result = normalize_parsed_data(raw_data)

        assert len(result.questions) == 1
        assert result.questions[0].id == 2


class TestFillRandomValue:

    def test_email_address_entry(self):
        result = fill_random_value(
            type_id=0, entry_id="emailAddress", options=None
        )
        assert result == "your_email@gmail.com"

    def test_short_answer_not_required(self):
        result = fill_random_value(
            type_id=0, entry_id="123", options=None, required=False
        )
        assert result == ""

    def test_short_answer_required(self):
        result = fill_random_value(
            type_id=0, entry_id="123", options=None, required=True
        )
        assert result == "Ok!"

    def test_multiple_choice_returns_one_option(self):
        options = ["A", "B", "C"]
        result = fill_random_value(type_id=2, entry_id="456", options=options)
        assert result in options

    def test_checkboxes_returns_subset(self):
        options = ["X", "Y", "Z"]
        result = fill_random_value(type_id=4, entry_id="789", options=options)
        assert isinstance(result, list)
        assert all(item in options for item in result)
        assert len(result) >= 1


class TestBuildGoogleFormPayload:

    def test_builds_correct_entry_keys(self):
        questions = [
            AnsweredQuestionStructure(
                id=100,
                question="Q1",
                type=QuestionType(type_id=0, description="Short answer"),
                required=True,
                user_answer="Hello",
            ),
            AnsweredQuestionStructure(
                id=200,
                question="Q2",
                type=QuestionType(type_id=2, description="Multiple choice"),
                required=False,
                llm_answer="B",
            ),
        ]

        result = build_google_form_payload(questions)

        assert result == {"entry.100": "Hello", "entry.200": "B"}

    def test_all_none_answers_produce_none_values(self):
        questions = [
            AnsweredQuestionStructure(
                id=300,
                question="Q3",
                type=QuestionType(type_id=1, description="Paragraph"),
                required=False,
            ),
        ]
        result = build_google_form_payload(questions)
        assert result == {"entry.300": None}


class TestGetRunStatus:

    @pytest.mark.asyncio
    @patch("app.controllers.tests.TEST_RUNS_JOBS_STORAGE", {})
    async def test_raises_not_found_for_missing_job(self):
        with pytest.raises(NotFoundError):
            await get_run_status("non-existent-id")

    @pytest.mark.asyncio
    @patch(
        "app.controllers.tests.TEST_RUNS_JOBS_STORAGE",
        {
            "job-123": {
                "status": JobStatus.COMPLETED,
                "processed_tests": 2,
                "total_tests": 2,
                "results": [{"run_id": 1, "status": "completed"}],
            }
        },
    )
    async def test_returns_completed_status_with_results(self):
        result = await get_run_status("job-123")

        assert result.job_id == "job-123"
        assert result.status == JobStatus.COMPLETED
        assert result.processed_runs_count == 2
        assert result.total_runs == 2
        assert result.results is not None

    @pytest.mark.asyncio
    @patch(
        "app.controllers.tests.TEST_RUNS_JOBS_STORAGE",
        {
            "job-456": {
                "status": JobStatus.PENDING,
                "processed_tests": 0,
                "total_tests": 5,
                "results": [],
            }
        },
    )
    async def test_returns_pending_status_without_results(self):
        result = await get_run_status("job-456")

        assert result.status == JobStatus.PENDING
        assert result.results is None
