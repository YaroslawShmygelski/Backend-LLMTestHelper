import datetime
import random

from fastapi import HTTPException
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm.test import Test
from app.models.orm.user import User
from app.schemas.test import TestContent, Question, QuestionType
from app.services.utils import get_form_type_description


def normalize_test_data(parsed_data: list[dict]) -> TestContent:
    normalized_questions: list[Question] = []
    for question in parsed_data:
        question_type_description_dict: QuestionType = get_form_type_description(
            question["type"]
        )
        normalized_questions.append(
            Question(
                id=question["id"],
                question=question["container_name"],
                required=question["required"],
                type=question_type_description_dict,
                options=question["options"],
            )
        )

    test_content = TestContent(questions=normalized_questions)
    return test_content


async def store_test_in_db(
    test_content: TestContent, current_user: User, async_db_session: AsyncSession
):
    test_db = Test(
        type="google_document",
        user_id=current_user.id,
        title="BoilerPlate",
        content=test_content,
    )
    async_db_session.add(test_db)
    await async_db_session.commit()
    return test_db


async def get_test_from_db(
    test_id: int, current_user: User, async_db_session: AsyncSession
) -> Test:
    result = await async_db_session.execute(
        Select(Test).where(Test.id == test_id, Test.user_id == current_user.id)
    )
    test_db = result.scalar_one_or_none()

    if not test_db:
        raise HTTPException(status_code=404, detail="Test not found")

    return test_db


def fill_random_value(type_id, entry_id, options, required=False, entry_name=""):
    """Fill random value for a form entry
    Customize your own fill_algorithm here
    Note: please follow this func signature to use as fill_algorithm in form.get_form_submit_request
    """
    # Customize for specific entry_id
    if entry_id == "emailAddress":
        return "your_email@gmail.com"
    if entry_name == "Short answer":
        return "Random answer!"
    # Random value for each type
    if type_id in [0, 1]:  # Short answer and Paragraph
        return "" if not required else "Ok!"
    if type_id == 2:  # Multiple choice
        return random.choice(options)
    if type_id == 3:  # Dropdown
        return random.choice(options)
    if type_id == 4:  # Checkboxes
        return random.sample(options, k=random.randint(1, len(options)))
    if type_id == 5:  # Linear scale
        return random.choice(options)
    if type_id == 7:  # Grid choice
        return random.choice(options)
    if type_id == 9:  # Date
        return datetime.date.today().strftime("z%Y-%m-%d")
    if type_id == 10:  # Time
        return datetime.datetime.now().strftime("%H:%M")
    return ""


def fill_form_entries(test_content: TestContent, fill_algorithm) -> TestContent:
    """Fill form entries with fill_algorithm"""
    for question in test_content.questions:
        options = question.options
        question.answer_mode = "random"
        question.random_answer = fill_algorithm(
            question.type.type_id,
            question.id,
            options,
            required=question.required,
            entry_name=question.question,
        )
    return test_content
