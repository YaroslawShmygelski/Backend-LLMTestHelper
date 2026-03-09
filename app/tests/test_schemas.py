import pytest
from unittest.mock import AsyncMock
from pydantic import ValidationError

from app.schemas.tests.test import (
    QuestionType,
    QuestionStructure,
    GoogleDocsRequest,
    TestSubmitPayload,
    Answer,
    JobResult,
)
from app.schemas.llm import LLMQuestionOut, LLMQuestionsListOut
from app.schemas.users import UserCreate
from app.utils.configs import get_form_type_description
from app.utils.exception_types import (
    BasicAppError,
    WrongRequestError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
    ServerError,
)
from app.services.tests.documents import check_request_document, extract_text_from_document
from app.settings import TXT_DOCUMENT_TYPE, PDF_DOCUMENT_TYPE, MAX_DOCUMENT_SIZE


class TestQuestionTypeSchema:

    def test_valid(self):
        qt = QuestionType(type_id=2, description="Multiple choice")
        assert qt.type_id == 2

    def test_missing_field(self):
        with pytest.raises(ValidationError):
            QuestionType(type_id=2)


class TestQuestionStructureSchema:

    def test_with_options(self):
        q = QuestionStructure(id=1, question="Q?", type=QuestionType(type_id=2, description="MC"), required=True, options=["A", "B"])
        assert q.options == ["A", "B"]

    def test_invalid_answer_mode(self):
        with pytest.raises(ValidationError):
            QuestionStructure(id=1, question="Q?", type=QuestionType(type_id=0, description="S"), required=False, answer_mode="invalid")


class TestTestSubmitPayloadSchema:

    def test_default_quantity(self):
        assert TestSubmitPayload(answers=[]).quantity == 1

    def test_custom_quantity(self):
        assert TestSubmitPayload(quantity=5, answers=[]).quantity == 5


class TestLLMSchemas:

    def test_str_answer(self):
        assert LLMQuestionOut(question_id=1, answer="Yes").answer == "Yes"

    def test_list_answer(self):
        assert LLMQuestionOut(question_id=1, answer=["A", "B"]).answer == ["A", "B"]


class TestUserCreateSchema:

    def test_valid(self):
        u = UserCreate(first_name="J", last_name="K", email="j@k.com", country_code=48, phone_number=123, password="longpassword")
        assert u.first_name == "J"

    def test_short_password(self):
        with pytest.raises(ValidationError):
            UserCreate(first_name="J", last_name="K", email="j@k.com", country_code=48, phone_number=123, password="short")

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(first_name="J", last_name="K", email="bad", country_code=48, phone_number=123, password="longpassword")


class TestFormTypeDescription:

    @pytest.mark.parametrize("type_id,expected", [
        (0, "Short answer"), (1, "Paragraph"), (2, "Multiple choice"),
        (3, "Dropdown"), (4, "Checkboxes"), (5, "Linear scale"),
        (7, "Grid choice"), (9, "Date"), (10, "Time"),
    ])
    def test_known_types(self, type_id, expected):
        result = get_form_type_description(type_id)
        assert result.type_id == type_id
        assert expected in result.description

    def test_unknown_type(self):
        assert get_form_type_description(999).description == "Type: Unknown"


class TestExceptions:

    @pytest.mark.parametrize("exc_cls,code", [
        (WrongRequestError, 400), (NotFoundError, 404), (UnauthorizedError, 401),
        (ForbiddenError, 403), (ConflictError, 409), (ServerError, 500),
    ])
    def test_status_codes(self, exc_cls, code):
        assert exc_cls.status_code == code

    def test_custom_message(self):
        err = NotFoundError("custom")
        assert err.message == "custom"
        assert str(err) == "custom"

    def test_inheritance(self):
        with pytest.raises(BasicAppError):
            raise UnauthorizedError("test")


class TestDocumentValidation:

    @pytest.mark.asyncio
    async def test_rejects_wrong_type(self):
        doc = AsyncMock()
        doc.content_type = "image/png"
        doc.read = AsyncMock(return_value=b"data")
        with pytest.raises(WrongRequestError):
            await check_request_document(doc)

    @pytest.mark.asyncio
    async def test_rejects_oversized(self):
        doc = AsyncMock()
        doc.content_type = TXT_DOCUMENT_TYPE
        doc.read = AsyncMock(return_value=b"x" * (MAX_DOCUMENT_SIZE + 1))
        with pytest.raises(WrongRequestError):
            await check_request_document(doc)

    @pytest.mark.asyncio
    async def test_accepts_valid_txt(self):
        doc = AsyncMock()
        doc.content_type = TXT_DOCUMENT_TYPE
        doc.read = AsyncMock(return_value=b"Hello")
        assert await check_request_document(doc) == b"Hello"


class TestTextExtraction:

    @pytest.mark.asyncio
    async def test_txt_decode(self):
        assert await extract_text_from_document(b"Hello world", TXT_DOCUMENT_TYPE) == "Hello world"

    @pytest.mark.asyncio
    async def test_txt_strips(self):
        assert await extract_text_from_document(b"  spaced  ", TXT_DOCUMENT_TYPE) == "spaced"

    @pytest.mark.asyncio
    async def test_invalid_pdf(self):
        assert await extract_text_from_document(b"not-pdf", PDF_DOCUMENT_TYPE) == ""
