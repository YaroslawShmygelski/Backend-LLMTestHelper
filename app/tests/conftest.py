import os
import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

os.environ.setdefault("SECRET_KEY", "test_secret_key_for_unit_tests_only")
os.environ.setdefault("AUTH_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test")

from app.database.models.orm.user import User
from app.database.models.orm.test import Test
from app.schemas.tests.test import (
    QuestionType,
    QuestionStructure,
    TestQuestions,
    Answer,
)


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.phone_number = 123456789
    user.country_code = 48
    user.is_active = True
    user.is_premium = False
    user.password_hash = "$argon2id$fake_hash"
    return user


@pytest.fixture
def sample_question_type():
    return QuestionType(type_id=2, description="Multiple choice (select one option)")


@pytest.fixture
def sample_questions(sample_question_type):
    return [
        QuestionStructure(
            id=100,
            question="What is Python?",
            type=sample_question_type,
            required=True,
            options=["A language", "A snake", "Both"],
        ),
        QuestionStructure(
            id=101,
            question="What is FastAPI?",
            type=QuestionType(type_id=0, description="Short answer (single-line text input)"),
            required=False,
            options=None,
        ),
    ]


@pytest.fixture
def sample_test_content(sample_questions):
    return TestQuestions(questions=sample_questions)


@pytest.fixture
def sample_parsed_data():
    return [
        {
            "id": 100,
            "container_name": "What is Python?",
            "name": "Python question",
            "type": 2,
            "required": True,
            "options": ["A language", "A snake", "Both"],
        },
        {
            "id": 101,
            "container_name": "What is FastAPI?",
            "name": "FastAPI question",
            "type": 0,
            "required": False,
            "options": None,
        },
        {
            "id": 999,
            "name": "Page break",
            "type": "pageBreak",
        },
    ]


@pytest.fixture
def mock_form_data_structure():
    return [
        None,
        [
            None,
            [
                [
                    None, "Your name", None, 0,
                    [[12345, None, 1]],
                ],
                [
                    None, "Favorite language", None, 2,
                    [[67890, [["Python"], ["JavaScript"], ["Go"]], 0]],
                ],
                [
                    None, "Section 2", None, 8, [],
                ],
            ],
        ],
    ]


@pytest.fixture
def mock_test_db(sample_test_content):
    test = MagicMock(spec=Test)
    test.id = 42
    test.type = "google_document"
    test.user_id = 1
    test.url = "https://docs.google.com/forms/d/e/test123/viewform"
    test.title = "Sample Test"
    test.content = sample_test_content
    test.is_submitted = False
    test.created_at = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    test.updated_at = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    return test


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def sample_answers():
    return [
        Answer(question_id=100, answer_mode="user", answer="A language"),
        Answer(question_id=101, answer_mode="random", answer=None),
    ]
