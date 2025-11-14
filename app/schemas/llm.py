from typing import Optional, List

from pydantic import BaseModel

from app.schemas.test import QuestionType


class LLMQuestionIn(BaseModel):
    id: int
    question: str
    type: QuestionType
    options: Optional[List[str]] = None


class LLMQuestionsListIn(BaseModel):
    questions: List[LLMQuestionIn]


class LLMQuestionOut(BaseModel):
    question_id: int
    answer: str | list[str]


class LLMQuestionsListOut(BaseModel):
    questions: List[LLMQuestionOut]
