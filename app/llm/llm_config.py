from typing import TypedDict, Optional, List

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from app.schemas.llm import  LLMQuestionOut, LLMQuestionsListIn

load_dotenv()


class LLMGeminiSettings(BaseSettings):
    MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0
    LLM_TIMEOUT: int = 30
    MAX_RETRIES: int = 2
    MAX_AGENT_RETRIES: int = 3



class LLMClient:
    def __init__(self):
        settings = LLMGeminiSettings()  # создаём экземпляр настроек

        self.model = ChatGoogleGenerativeAI(
            model=settings.MODEL,
            temperature=settings.LLM_TEMPERATURE,
            timeout=settings.LLM_TIMEOUT,
            max_retries=settings.MAX_RETRIES,
        )

    def invoke_llm(self, prompt: str) -> str:
        response = self.model.invoke(prompt)
        result = response.content.strip()
        print(f"{result=}")
        return result

class LLMSolverState(BaseModel):
    questions: LLMQuestionsListIn
    raw_answers: Optional[str] = None
    validated_answers: Optional[List[LLMQuestionOut]] = None
    attempts: int = 0
    errors: Optional[str] = None


# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
# )
# data = [{"id": 1187272786, "type": {"type_id": 2, "description": "Multiple choice (select one option)"},
#          "options": ["prog", "creep", "looser", "clown"], "question": "Who are you",
#          "required": "false", "answer_mode": None}]
#
LLM_SYSTEM_MESSAGE = """
You are the intelligent assistant of a Test Solving app.
You are given a list of questions in JSON format below:"""

LLM_SOLVER_RESPONSE_RULES = """
  Rules:
- If options exist, choose one
- If not, generate a concise answer
- Do NOT add any explanations, Markdown, or Python code"""

# prompt = f"""
# You are the intelligent assistant of a Test Solving app.
#
# You are given a list of questions in JSON format below:
# {json.dumps(data, indent=2)}
#
# Please answer EACH question and return the result strictly as a JSON array.
# Each element must look like this:
# {{
#   "question_id": <type_id>,
#   "answer": "<your chosen or generated answer>"
# }}
#
# Rules:
# - Always choose the most logical or correct answer from provided options.
# - If no options exist, generate one concise answer yourself.
# - Return ONLY a valid JSON array — no markdown, no ```json, no explanations.
# If you include anything else (like text or backticks), the system will reject it.
# """
#
# # response = llm.invoke(prompt)
# # print(response)
# # print(response.content)
#
# # raw_output = response.content.strip()
# # clean_output = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_output.strip())
#
# # try:
# #     result = json.loads(raw_output)
# #     print("valid")
# #     print(result)
# # except json.JSONDecodeError as e:
# #     print("❌ Ошибка разбора JSON:", e)
# #     print("not valid")
# #     print(raw_output)
#
# question = LLMQuestionIn(
#     **{"id": 1187272786, "type": {"type_id": 2, "description": "Multiple choice (select one option)"},
#      "options": ["prog", "creep", "looser", "clown"], "question": "Who are you"})
# print(question)
# print(question.model_dump(exclude_none=True))
