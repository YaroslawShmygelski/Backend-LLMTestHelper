import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel


class QuestionType(BaseModel):
    type_id: int
    description: str


class QuestionStructure(BaseModel):
    id: int
    question: str
    type: QuestionType
    required: bool
    options: Optional[List[str]] = None
    answer_mode: Optional[Literal["llm", "random", "user"]] = None


class AnsweredQuestionStructure(QuestionStructure):
    user_answer: Optional[str] | Optional[list] = None
    llm_answer: Optional[str] | Optional[list] = None
    random_answer: Optional[str] | Optional[list] = None


class TestContent(BaseModel):
    questions: List[QuestionStructure]


class AnsweredTestContent(BaseModel):
    questions: List[AnsweredQuestionStructure]


class TestResponse(BaseModel):
    test_id: int
    run_id: Optional[int] = None


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
    answer: Optional[str] | Optional[list] = None


class TestSubmitPayload(BaseModel):
    quantity: Optional[int] = 1
    answers: list[Answer]


class TestGetResponse(BaseModel):
    test_id: int
    test_structure: TestContent
    uploaded_date: datetime.datetime


class TestRunResponse(BaseModel):
    test_id: int
    run_id: int
    run_content: AnsweredTestContent
    llm_model: Optional[str] = None
    submitted_date: datetime.datetime


class SubmitTestResponse(BaseModel):
    job_id: str
    message: str


class JobResult(BaseModel):
    run_id: int
    status: str
    error: str | None = None


class RunJobStatusResponse(BaseModel):
    job_id: str
    status: str
    processed_runs_count: int
    total_runs: int
    results: Optional[List[JobResult]] = None


class RunsOfTest(BaseModel):
    run_id: int
    test_id: int
    user_id: int
    job_id: str
    submitted_date: datetime.datetime
    llm_model: Optional[str] = None


class RunsOfTestResponse(BaseModel):
    test_runs: list[RunsOfTest]
