from typing import List, Optional, Literal

from pydantic import BaseModel


class QuestionType(BaseModel):
    type_id: int
    description: str


class Question(BaseModel):
    id: int
    question: str
    type: QuestionType
    required: bool
    options: Optional[List[str]] = None
    answer_mode: Optional[Literal["llm", "random", "user"]] = None
    user_answer: Optional[str] | Optional[list] = None
    llm_answer: Optional[str] | Optional[list] = None
    random_answer: Optional[str] | Optional[list] = None


class TestContent(BaseModel):
    questions: List[Question]


class TestUploadOutput(BaseModel):
    id: int


class GoogleDocsRequest(BaseModel):
    test_url: str


class TestUpdate(BaseModel):
    type: Optional[str] = None
    user_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[TestContent] = None

class Answer(BaseModel):
    question_id: int
    answer_mode: Optional[Literal["llm", "random", "user"]] = None
    answer: Optional[str] = None


class TestSubmitPayload(BaseModel):
    quantity: Optional[int] = 1
    answers: list[Answer]


class TestSubmittedOutput(BaseModel):
    id: int