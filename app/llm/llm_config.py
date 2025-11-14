from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from app.schemas.llm import LLMQuestionsListOut, LLMQuestionsListIn

load_dotenv()


@dataclass
class LLMGeminiSettings:
    MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0
    LLM_TIMEOUT: int = 30
    MAX_RETRIES: int = 2
    MAX_AGENT_RETRIES: int = 3


class LLMClient:
    def __init__(self):

        self.model = ChatGoogleGenerativeAI(
            model=LLMGeminiSettings.MODEL,
            temperature=LLMGeminiSettings.LLM_TEMPERATURE,
            timeout=LLMGeminiSettings.LLM_TIMEOUT,
            max_retries=LLMGeminiSettings.MAX_RETRIES,
        )

    def invoke_llm(self, prompt: str) -> str:
        response = self.model.invoke(prompt)
        result = response.content.strip()
        print(f"{result=}")
        return result


class LLMSolverState(BaseModel):
    questions: LLMQuestionsListIn
    raw_answers: Optional[str] = None
    validated_answers: Optional[LLMQuestionsListOut] = None
    attempts: int = 0
    error: Optional[str] = None

    def increment_attempts(self):
        self.attempts += 1


def build_test_solver_prompt(questions: LLMQuestionsListIn) -> str:
    return f"""
            {LLM_SYSTEM_MESSAGE}
            Questions:
            {questions.model_dump()}
            Return ONLY a JSON array matching this Pydantic schema:
            {LLMQuestionsListOut.model_json_schema()}
            {LLM_SOLVER_RESPONSE_RULES}
            """


LLM_SYSTEM_MESSAGE = """
You are the intelligent assistant of a Test Solving app.
You are given a list of questions in JSON format below:"""

LLM_SOLVER_RESPONSE_RULES = """
  Rules:
- If options exist, choose one or many depending on type description
- if there is option where you have to select multiple answers you should send "answer": ["option1", "option2"]]
- If not, generate a concise answer
- ALLWAYS Do NOT add any explanations, Markdowns, //, or Python code"""
