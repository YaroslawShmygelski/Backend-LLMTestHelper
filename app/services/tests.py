import datetime
import random

from fastapi import HTTPException
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.llm_config import LLMClient, LLMSolverState
from app.llm.llm_test_solver import LLMTestSolverAgent
from app.models.orm.test import Test
from app.models.orm.user import User
from app.schemas.llm import LLMQuestionIn, LLMQuestionsListIn
from app.schemas.test import (
    TestContent,
    QuestionStructure,
    QuestionType,
    Answer,
    AnsweredTestContent,
    AnsweredQuestionStructure,
)
from app.utils.configs import get_form_type_description


def normalize_test_data(parsed_data: list[dict]) -> TestContent:
    normalized_questions: list[QuestionStructure] = []
    for question in parsed_data:
        question_type_description_dict: QuestionType = get_form_type_description(
            question["type"]
        )
        normalized_questions.append(
            QuestionStructure(
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
    test_content: TestContent,
    test_url: str,
    current_user: User,
    async_db_session: AsyncSession,
):
    test_db = Test(
        type="google_document",
        user_id=current_user.id,
        url=test_url,
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


# pylint: disable=too-many-return-statements
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


def answer_llm_questions(llm_input_questions: list[QuestionStructure]):
    if llm_input_questions:
        llm_questions_list_in = LLMQuestionsListIn(
            questions=[
                LLMQuestionIn(
                    id=q.id, question=q.question, type=q.type, options=q.options
                )
                for q in llm_input_questions
            ]
        )

        llm_client = LLMClient()
        solver_agent = LLMTestSolverAgent(llm_client)

        state = LLMSolverState(questions=llm_questions_list_in)

        result_state: LLMSolverState = solver_agent.call_llm(state)
        validated_llm_answers = result_state.get("validated_answers")
        llm_answers_map = {
            q.question_id: q.answer for q in validated_llm_answers.questions
        }

        return llm_answers_map
    return None


def answer_test_questions(
    test_content: TestContent, payload_answers: list[Answer]
) -> AnsweredTestContent:
    """Fill form entries with fill_algorithm"""
    answers_map = {a.question_id: a for a in payload_answers}
    answered_questions = []
    llm_input_questions = []
    for question in test_content.questions:
        answered_question = AnsweredQuestionStructure(
            id=question.id,
            question=question.question,
            type=question.type,
            required=question.required,
            options=question.options,
            answer_mode=None,
            user_answer=None,
            llm_answer=None,
            random_answer=None,
        )
        payload = answers_map.get(question.id)
        if payload and payload.answer_mode:
            if payload.answer_mode == "user":
                answered_question.answer_mode = "user"
                answered_question.user_answer = payload.answer
            elif payload.answer_mode == "random":
                answered_question.answer_mode = "random"
                answered_question.random_answer = fill_random_value(
                    question.type.type_id,
                    question.id,
                    question.options,
                    required=question.required,
                    entry_name=question.question,
                )
            elif payload.answer_mode == "llm":
                answered_question.answer_mode = "llm"
                llm_input_questions.append(question)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown answer_mode '{payload.answer_mode}'"
                    f"for question {question.id}",
                )
        answered_questions.append(answered_question)

    llm_answers_map = answer_llm_questions(llm_input_questions)

    for aq in answered_questions:
        if aq.answer_mode == "llm" and aq.id in llm_answers_map:
            aq.llm_answer = llm_answers_map[aq.id]

    return AnsweredTestContent(questions=answered_questions)
