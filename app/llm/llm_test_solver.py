import json
import logging

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from pydantic import TypeAdapter, ValidationError
from app.llm.llm_config import (
    LLMClient,
    LLMSolverState,
    build_test_solver_prompt,
    LLMGeminiSettings,
)
from app.schemas.llm import (
    LLMQuestionsListIn,
    LLMQuestionsListOut,
)

logger = logging.getLogger(__name__)


class LLMTestSolverAgent:
    def __init__(self, llm_model: LLMClient):
        self.llm_model = llm_model
        self.workflow = StateGraph(LLMSolverState)

    @staticmethod
    def __create_prompt(questions: LLMQuestionsListIn) -> str:
        message = build_test_solver_prompt(questions)
        return message

    def generate_attempt(self, state: LLMSolverState) -> LLMSolverState:
        prompt = self.__create_prompt(state.questions)
        if state.error:
            prompt += f"\nPlease change you answers it solver error in previous call:{state.error}"
        logger.info(f"Generating attempt with prompt", extra={"prompt": prompt})
        state.raw_answers = self.llm_model.invoke_llm(prompt)
        return state

    @staticmethod
    def validate_llm_answer(state: LLMSolverState) -> LLMSolverState:
        try:
            parsed = json.loads(state.raw_answers)
            validated_data = TypeAdapter(LLMQuestionsListOut).validate_python(parsed)
            state.validated_answers = validated_data
            state.error = None
        except ValidationError as e:
            state.increment_attempts()
            state.error = str(e)
            if state.attempts >= LLMGeminiSettings.MAX_RETRIES:
                state.error = f"Reached Maximum retries with error {e}"
                logger.error(
                    "LLM reached Maximum retries with error",
                    extra={"error": state.error},
                )
        return state

    @staticmethod
    def decision_edge(state: LLMSolverState) -> str:
        return "retry" if state.error else "success"

    def _build_graph(self) -> CompiledStateGraph:
        self.workflow.add_node("generate_attempt", self.generate_attempt)
        self.workflow.add_node("validate_llm_answer", self.validate_llm_answer)
        self.workflow.add_edge("generate_attempt", "validate_llm_answer")
        self.workflow.add_conditional_edges(
            "validate_llm_answer",
            self.decision_edge,
            {"retry": "generate_attempt", "success": END},
        )
        self.workflow.set_entry_point("generate_attempt")

        compiled_graph = self.workflow.compile()
        return compiled_graph

    def call_llm(self, state: LLMSolverState) -> LLMSolverState:
        res = self._build_graph()
        result = res.invoke(state)
        logger.info(f"LLM Generation Result", extra={"result": result})
        return result
