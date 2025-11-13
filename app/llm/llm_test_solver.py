from langgraph.graph import StateGraph,END
from pydantic import parse_obj_as, TypeAdapter, ValidationError
from IPython.display import Image, display
from app.llm.llm_config import LLMClient, LLMSolverState, LLM_SYSTEM_MESSAGE, LLM_SOLVER_RESPONSE_RULES, LLMGeminiSettings
from app.schemas.llm import LLMQuestionIn, LLMQuestionsListIn, LLMQuestionOut, LLMQuestionsListOut


class LLMTestSolverAgent:
    def __init__(self, llm_model: LLMClient):
        self.llm_model = llm_model
        self.workflow = StateGraph(LLMSolverState)
    @staticmethod
    def __create_prompt(questions: LLMQuestionsListIn) -> str:
        message = f"""
            {LLM_SYSTEM_MESSAGE}
            Questions:
            {questions.model_dump()}
            Return ONLY a JSON array matching this schema:
            {LLMQuestionsListOut.model_json_schema()}
            {LLM_SOLVER_RESPONSE_RULES}
            """
        print(message)
        return message

    def generate_attempt(self, state: LLMSolverState) -> LLMSolverState:
        prompt = self.__create_prompt(state.questions)
        if state.errors:
            prompt += f"\nPlease change you answers it solver error in previous call:{state['errors']}"
        state.raw_answers = self.llm_model.invoke_llm(prompt)
        state.attempts += 1
        return state

    @staticmethod
    def validate_llm_answer(state: LLMSolverState) -> LLMSolverState | str:
        try:
            validated_data =TypeAdapter(LLMQuestionsListOut).validate_python(state["raw_answers"])
            print(validated_data)
            state.validated_answers=validated_data
            state.errors = None
            return state
        except ValidationError as e:
            state.errors = str(e)
            if state.attempts >= LLMGeminiSettings.MAX_ATTEMPTS:
                return "unable to solve the requested questions"
            return state

    @staticmethod
    def decision_edge(state: LLMSolverState) -> str:
        if state.errors:
            return "retry"
        else:
            return "success"


    def _build_graph(self):

        self.workflow.add_node("generate_attempt", self.generate_attempt)
        self.workflow.add_node("validate_llm_answer", self.validate_llm_answer)
        self.workflow.add_conditional_edges("generate_attempt", self.decision_edge,
                                       {"retry":"validate_llm_answer", "success": END})
        self.workflow.set_entry_point("generate_attempt")

        self.workflow=self.workflow.compile()
        graph_obj = self.workflow.get_graph()  # или self.__graph.get_graph() если внутри класса

        # Сгенерировать PNG через Mermaid
        png_bytes = graph_obj.draw_mermaid_png()

        # Показать в Jupyter
        display(Image(png_bytes))
        print(self.workflow)
        return self.workflow

    def solve(self, state: LLMSolverState):
        res=self._build_graph()
        result = res.invoke(state)
        return result