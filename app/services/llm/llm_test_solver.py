import asyncio
import json
import logging

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm.embeddings import retrieve_context_from_db
from app.services.llm.llm_config import (
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
    def __init__(self, llm_model: LLMClient, test_id: int, db_session: AsyncSession):
        self.llm_model = llm_model
        self.test_id = test_id
        self.db_session = db_session
        self.workflow = StateGraph(LLMSolverState)

    async def retrieve_context(self, state: LLMSolverState) -> LLMSolverState:
        questions_text = " ".join(q.question for q in state.questions.questions)

        chunks_db = await retrieve_context_from_db(
            question_text=questions_text,
            db_session=self.db_session,
            test_id=self.test_id,
        )
        if chunks_db:
            state.context_chunks = chunks_db
        logger.info(
            "Retrieved context",
            extra={
                "chunks_count": len(state.context_chunks),
                "test_id": self.test_id,
            },
        )

        return state

    @staticmethod
    def __create_prompt(
        questions: LLMQuestionsListIn, context_chunks: list[str]
    ) -> str:
        message = build_test_solver_prompt(questions, context_chunks)
        return message

    def generate_attempt(self, state: LLMSolverState) -> LLMSolverState:
        prompt = self.__create_prompt(state.questions, state.context_chunks)
        if state.error:
            prompt += f"\nPlease change you answers it solver error in previous call:{state.error}"
        logger.info(
            "Generating LLM attempt",
            extra={"attempt": state.attempts + 1, "prompt": prompt},
        )
        state.raw_answers = self.llm_model.invoke_llm(prompt)
        return state

    @staticmethod
    def validate_llm_answer(state: LLMSolverState) -> LLMSolverState:
        try:
            parsed = json.loads(state.raw_answers)
            validated_data = TypeAdapter(LLMQuestionsListOut).validate_python(parsed)
            state.validated_answers = validated_data
            state.error = None
        except (json.JSONDecodeError, ValidationError) as e:
            state.increment_attempts()
            state.error = str(e)

            logger.warning(
                "LLM validation failed",
                extra={"attempt": state.attempts, "error": state.error},
            )

            if state.attempts >= LLMGeminiSettings.max_retries:
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
        self.workflow.add_node("retrieve_context", self.retrieve_context)
        self.workflow.add_node("generate_attempt", self.generate_attempt)
        self.workflow.add_node("validate_llm_answer", self.validate_llm_answer)

        self.workflow.set_entry_point("retrieve_context")

        self.workflow.add_edge("retrieve_context", "generate_attempt")
        self.workflow.add_edge("generate_attempt", "validate_llm_answer")

        self.workflow.add_conditional_edges(
            "validate_llm_answer",
            lambda s: "retry" if s.error else "success",
            {
                "retry": "generate_attempt",
                "success": END,
            },
        )

        compiled_graph = self.workflow.compile()

        png_bytes = compiled_graph.get_graph().draw_mermaid_png()

        with open("llm_solver_graph.png", "wb") as f:
            f.write(png_bytes)
        return compiled_graph

    async def call_llm_async(self, state: LLMSolverState) -> LLMSolverState:
        graph = self._build_graph()
        result = await graph.ainvoke(state)
        return result
