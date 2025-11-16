import logging
from datetime import datetime, UTC

import requests
from fastapi import HTTPException
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm.test_run import TestRun
from app.models.orm.user import User
from app.parsers.google_form import parse_form_entries, get_form_response_url
from app.schemas.test import (
    TestResponse,
    GoogleDocsRequest,
    TestContent,
    TestUpdate,
    TestSubmitPayload,
    TestGetResponse,
    TestRunResponse,
)
from app.services.tests import (
    normalize_test_data,
    store_test_in_db,
    get_test_from_db,
    answer_test_questions,
)
from app.utils.exception_types import ServerError
from app.utils.logging import correlation_id

logger = logging.getLogger(__name__)


async def upload_google_doc_test(
    payload: GoogleDocsRequest, current_user: User, async_db_session: AsyncSession
) -> TestResponse:
    logger.info(
        "google_doc_import",
        extra={
            "user_id": current_user.id,
            "test_url": payload.test_url,
        },
    )
    parsed_data = parse_form_entries(url=payload.test_url, only_required=False)

    test_content: TestContent = normalize_test_data(parsed_data)

    test_db = await store_test_in_db(
        test_content=test_content,
        test_url=payload.test_url,
        current_user=current_user,
        async_db_session=async_db_session,
    )

    logger.info(
        "Test saved to DB",
        extra={
            "test_id": test_db.id,
            "user_id": current_user.id,
            "test_url": payload.test_url,
        },
    )

    return TestResponse(id=test_db.id)


async def get_test(
    test_id: int, current_user: User, db_session: AsyncSession
) -> TestGetResponse:
    test_db = await get_test_from_db(
        test_id=test_id, current_user=current_user, async_db_session=db_session
    )

    logger.info(
        "Test retrieved from DB",
        extra={
            "test_id": test_db.id,
            "user_id": current_user.id,
        },
    )
    return TestGetResponse(
        test_id=test_db.id,
        test_structure=test_db.content,
        uploaded_date=test_db.created_at,
    )


async def update_test(
    test_id: int, update_data: TestUpdate, current_user: User, db_session: AsyncSession
) -> TestResponse:
    test_db = await get_test_from_db(
        test_id=test_id, current_user=current_user, async_db_session=db_session
    )

    logger.info(
        "Updating test",
        extra={
            "test_id": test_db.id,
            "user_id": current_user.id,
            "updated_fields": list(update_data.model_dump(exclude_none=True).keys()),
        },
    )

    for key, value in update_data.model_dump(exclude_none=True).items():
        setattr(test_db, key, value)

    await db_session.commit()
    await db_session.refresh(test_db)

    logger.info(
        "Test updated successfully",
        extra={
            "test_id": test_db.id,
            "user_id": current_user.id,
        },
    )

    return TestResponse(id=test_db.id)


async def submit_test(
    test_id: int,
    payload: TestSubmitPayload,
    current_user: User,
    db_session: AsyncSession,
) -> TestResponse:
    test_db = await get_test_from_db(
        test_id=test_id, current_user=current_user, async_db_session=db_session
    )

    logger.info(
        "Submitting test",
        extra={
            "test_id": test_db.id,
            "user_id": current_user.id,
        },
    )

    answered_test_content = answer_test_questions(
        test_content=test_db.content, payload_answers=payload.answers
    )

    data = {}
    for entry in answered_test_content.questions:
        value = entry.user_answer or entry.llm_answer or entry.random_answer or None

        data[f"entry.{entry.id}"] = value

    if test_db.url:
        formed_url: str = get_form_response_url(url=test_db.url)
        res = requests.post(url=formed_url, data=data, timeout=5)
        if res.status_code != 200:
            logger.error(
                "Error submitting test to Google form",
                extra={
                    "test_id": test_db.id,
                    "user_id": current_user.id,
                    "status_code": res.status_code,
                    "url": test_db.url,
                },
            )
            raise ServerError(message="Error submitting test to Google form")

    test_db.is_submitted = True
    answered_test_db = TestRun(
        test_id=test_db.id,
        user_id=current_user.id,
        run_content=answered_test_content,
        submitted_date=datetime.now(UTC),
    )

    db_session.add(answered_test_db)
    await db_session.commit()
    await db_session.refresh(test_db)

    logger.info(
        "Test submitted successfully",
        extra={
            "test_id": test_db.id,
            "run_id": answered_test_db.id,
            "user_id": current_user.id,
            "correlation_id": correlation_id.get(),
        },
    )

    return TestResponse(id=test_db.id, run_id=answered_test_db.id)


async def get_test_run(run_id: int, current_user: User, db_session: AsyncSession):
    query = await db_session.execute(
        Select(TestRun).where(TestRun.id == run_id, TestRun.user_id == current_user.id)
    )
    test_run_db = query.scalar_one_or_none()

    logger.info(
        "TestRun retrieved",
        extra={
            "run_id": test_run_db.id,
            "test_id": test_run_db.test_id,
            "user_id": current_user.id,
            "correlation_id": correlation_id.get(),
        },
    )
    return TestRunResponse(
        test_id=test_run_db.test_id,
        run_id=test_run_db.id,
        run_content=test_run_db.run_content,
        submitted_date=test_run_db.submitted_date,
    )
