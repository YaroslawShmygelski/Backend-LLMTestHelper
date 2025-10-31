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
