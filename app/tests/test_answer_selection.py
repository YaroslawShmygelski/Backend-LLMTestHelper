import pytest
from fastapi import HTTPException

from app.schemas.tests.test import (
    QuestionType,
    AnsweredQuestionStructure,
    AnsweredTestContent,
    Answer,
)
from app.services.tests.tests import (
    fill_random_value,
    build_google_form_payload,
    answer_test_questions,
)


class TestFillRandomValue:

    def test_email_entry(self):
        assert "@" in fill_random_value(0, "emailAddress", None)

    def test_short_answer_required(self):
        assert fill_random_value(0, "x", None, required=True) == "Ok!"

    def test_short_answer_not_required(self):
        assert fill_random_value(0, "x", None, required=False) == ""

    def test_paragraph_required(self):
        assert fill_random_value(1, "x", None, required=True) == "Ok!"

    def test_multiple_choice(self):
        opts = ["A", "B", "C"]
        assert fill_random_value(2, "x", opts) in opts

    def test_dropdown(self):
        opts = ["X", "Y"]
        assert fill_random_value(3, "x", opts) in opts

    def test_checkboxes_returns_list(self):
        opts = ["A", "B", "C", "D"]
        result = fill_random_value(4, "x", opts)
        assert isinstance(result, list)
        assert 1 <= len(result) <= len(opts)
        assert all(o in opts for o in result)

    def test_linear_scale(self):
        opts = ["1", "2", "3", "4", "5"]
        assert fill_random_value(5, "x", opts) in opts

    def test_grid_choice(self):
        opts = ["Row 1", "Row 2"]
        assert fill_random_value(7, "x", opts) in opts

    def test_date_format(self):
        result = fill_random_value(9, "x", None)
        assert result.startswith("z")
        assert len(result) == 11

    def test_time_format(self):
        result = fill_random_value(10, "x", None)
        assert ":" in result

    def test_unknown_type(self):
        assert fill_random_value(99, "x", None) == ""


class TestBuildGoogleFormPayload:

    def _q(self, qid, mode, user=None, llm=None, random=None):
        return AnsweredQuestionStructure(
            id=qid, question="Q?",
            type=QuestionType(type_id=0, description="Short"),
            required=False, answer_mode=mode,
            user_answer=user, llm_answer=llm, random_answer=random,
        )

    def test_user_answer(self):
        result = build_google_form_payload([self._q(100, "user", user="ans")])
        assert result["entry.100"] == "ans"

    def test_llm_answer(self):
        result = build_google_form_payload([self._q(200, "llm", llm="llm_ans")])
        assert result["entry.200"] == "llm_ans"

    def test_random_answer(self):
        result = build_google_form_payload([self._q(300, "random", random="rand")])
        assert result["entry.300"] == "rand"

    def test_priority_user_over_llm(self):
        result = build_google_form_payload([self._q(100, "user", user="U", llm="L")])
        assert result["entry.100"] == "U"

    def test_no_answer(self):
        result = build_google_form_payload([self._q(100, None)])
        assert result["entry.100"] is None

    def test_multiple_entries(self):
        qs = [
            self._q(1, "user", user="A1"),
            self._q(2, "llm", llm="A2"),
            self._q(3, "random", random="A3"),
        ]
        result = build_google_form_payload(qs)
        assert len(result) == 3


class TestAnswerTestQuestions:

    @pytest.mark.asyncio
    async def test_user_mode(self, sample_test_content, mock_db_session):
        answers = [
            Answer(question_id=100, answer_mode="user", answer="A language"),
            Answer(question_id=101, answer_mode="user", answer="Framework"),
        ]
        result = await answer_test_questions(
            test_content=sample_test_content, payload_answers=answers,
            test_id=42, db_session=mock_db_session,
        )
        assert isinstance(result, AnsweredTestContent)
        assert result.questions[0].answer_mode == "user"
        assert result.questions[0].user_answer == "A language"

    @pytest.mark.asyncio
    async def test_random_mode(self, sample_test_content, mock_db_session):
        answers = [
            Answer(question_id=100, answer_mode="random"),
            Answer(question_id=101, answer_mode="random"),
        ]
        result = await answer_test_questions(
            test_content=sample_test_content, payload_answers=answers,
            test_id=42, db_session=mock_db_session,
        )
        assert result.questions[0].answer_mode == "random"
        assert result.questions[0].random_answer in ["A language", "A snake", "Both"]

    @pytest.mark.asyncio
    async def test_no_answer_leaves_none(self, sample_test_content, mock_db_session):
        result = await answer_test_questions(
            test_content=sample_test_content, payload_answers=[],
            test_id=42, db_session=mock_db_session,
        )
        for q in result.questions:
            assert q.answer_mode is None
            assert q.user_answer is None

    @pytest.mark.asyncio
    async def test_mixed_modes(self, sample_test_content, mock_db_session):
        answers = [
            Answer(question_id=100, answer_mode="user", answer="Manual"),
            Answer(question_id=101, answer_mode="random"),
        ]
        result = await answer_test_questions(
            test_content=sample_test_content, payload_answers=answers,
            test_id=42, db_session=mock_db_session,
        )
        assert result.questions[0].answer_mode == "user"
        assert result.questions[1].answer_mode == "random"

    @pytest.mark.asyncio
    async def test_unknown_mode_raises_400(self, sample_test_content, mock_db_session):
        answers = [Answer(question_id=100, answer_mode="user", answer="ok")]
        answers[0].answer_mode = "telekinesis"
        with pytest.raises(HTTPException) as exc:
            await answer_test_questions(
                test_content=sample_test_content, payload_answers=answers,
                test_id=42, db_session=mock_db_session,
            )
        assert exc.value.status_code == 400
