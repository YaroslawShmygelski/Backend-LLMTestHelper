import json
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.schemas.llm import LLMQuestionIn, LLMQuestionsListIn
from app.schemas.tests.test import QuestionType
from app.services.llm.llm_config import (
    LLMSolverState,
    LLMGeminiSettings,
    build_test_solver_prompt,
)
from app.services.llm.llm_test_solver import LLMTestSolverAgent


@pytest.fixture
def llm_questions():
    return LLMQuestionsListIn(
        questions=[
            LLMQuestionIn(
                id=1, question="What is Python?",
                type=QuestionType(type_id=2, description="MC"),
                options=["Language", "Snake"],
            )
        ]
    )


@pytest.fixture
def solver_state(llm_questions):
    return LLMSolverState(questions=llm_questions)


@pytest.fixture
def agent():
    return LLMTestSolverAgent(
        llm_model=MagicMock(), test_id=1, db_session=AsyncMock()
    )


class TestLLMSolverState:

    def test_defaults(self, llm_questions):
        state = LLMSolverState(questions=llm_questions)
        assert state.attempts == 0
        assert state.error is None
        assert state.raw_answers is None
        assert state.validated_answers is None
        assert state.context_chunks == []

    def test_increment_attempts(self, solver_state):
        solver_state.increment_attempts()
        assert solver_state.attempts == 1
        solver_state.increment_attempts()
        assert solver_state.attempts == 2


class TestBuildPrompt:

    def test_contains_questions(self, llm_questions):
        prompt = build_test_solver_prompt(llm_questions, [])
        assert "What is Python?" in prompt

    def test_contains_context(self, llm_questions):
        prompt = build_test_solver_prompt(llm_questions, ["Python is a language."])
        assert "Python is a language." in prompt

    def test_no_context_section_when_empty(self, llm_questions):
        prompt = build_test_solver_prompt(llm_questions, [])
        assert "additional context" not in prompt

    def test_contains_schema(self, llm_questions):
        prompt = build_test_solver_prompt(llm_questions, [])
        assert "question_id" in prompt

    def test_contains_rules(self, llm_questions):
        prompt = build_test_solver_prompt(llm_questions, [])
        assert "Rules" in prompt


class TestValidateLLMAnswer:

    def test_valid_json(self, solver_state):
        solver_state.raw_answers = json.dumps(
            {"questions": [{"question_id": 1, "answer": "Language"}]}
        )
        result = LLMTestSolverAgent.validate_llm_answer(solver_state)
        assert result.error is None
        assert result.validated_answers is not None
        assert result.validated_answers.questions[0].answer == "Language"

    def test_invalid_json(self, solver_state):
        solver_state.raw_answers = "not valid json {{"
        result = LLMTestSolverAgent.validate_llm_answer(solver_state)
        assert result.error is not None
        assert result.attempts == 1

    def test_wrong_schema(self, solver_state):
        solver_state.raw_answers = json.dumps({"wrong_key": "value"})
        result = LLMTestSolverAgent.validate_llm_answer(solver_state)
        assert result.error is not None
        assert result.attempts == 1

    def test_max_retries(self, solver_state):
        solver_state.raw_answers = "bad"
        solver_state.attempts = LLMGeminiSettings.max_retries - 1
        result = LLMTestSolverAgent.validate_llm_answer(solver_state)
        assert "Maximum retries" in result.error

    def test_list_answer(self, solver_state):
        solver_state.raw_answers = json.dumps(
            {"questions": [{"question_id": 1, "answer": ["Language", "Snake"]}]}
        )
        result = LLMTestSolverAgent.validate_llm_answer(solver_state)
        assert result.error is None
        assert result.validated_answers.questions[0].answer == ["Language", "Snake"]


class TestDecisionEdge:

    def test_retry_on_error(self, solver_state):
        solver_state.error = "Some error"
        assert LLMTestSolverAgent.decision_edge(solver_state) == "retry"

    def test_success_on_no_error(self, solver_state):
        solver_state.error = None
        assert LLMTestSolverAgent.decision_edge(solver_state) == "success"


class TestGenerateAttempt:

    def test_calls_invoke(self, agent, solver_state):
        agent.llm_model.invoke_llm = MagicMock(return_value='{"questions": []}')
        result = agent.generate_attempt(solver_state)
        agent.llm_model.invoke_llm.assert_called_once()
        assert result.raw_answers == '{"questions": []}'

    def test_appends_error_on_retry(self, agent, solver_state):
        solver_state.error = "JSON parse error"
        agent.llm_model.invoke_llm = MagicMock(return_value='{"questions": []}')
        agent.generate_attempt(solver_state)
        prompt = agent.llm_model.invoke_llm.call_args[0][0]
        assert "JSON parse error" in prompt
