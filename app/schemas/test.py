from typing import List, Optional, Literal

from pydantic import BaseModel


class QuestionType(BaseModel):
    type_id: int
    description: str


class Question(BaseModel):
    id: int
    question: str
    type: QuestionType
    options: Optional[List[str]] = None
    answer_mode: Optional[Literal["llm", "random", "user"]] = None
    user_answer: Optional[str] = None
    llm_answer: Optional[str] = None
    random_answer: Optional[str] = None


class TestContent(BaseModel):
    questions: List[Question]


class TestUploadOutput(BaseModel):
    id: int
    status_code: Literal[201, 400, 500]


class GoogleDocsRequest(BaseModel):
    link: str
