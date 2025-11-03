import requests
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm.user import User
from app.parsers.google_form import parse_form_entries, get_form_response_url
from app.schemas.test import (
    TestUploadOutput,
    GoogleDocsRequest,
    TestContent,
    TestUpdate,
    TestSubmitPayload,
)
from app.services.tests import (
    normalize_test_data,
    store_test_in_db,
    get_test_from_db,
    fill_form_entries,

)


async def upload_google_doc_test(
        payload: GoogleDocsRequest, current_user: User, async_db_session: AsyncSession
) -> TestUploadOutput:
    parsed_data = parse_form_entries(url=payload.test_url, only_required=False)

    test_content: TestContent = normalize_test_data(parsed_data)

    test_db = await store_test_in_db(
        test_content=test_content,
        test_url=payload.test_url,
        current_user=current_user,
        async_db_session=async_db_session,
    )

    return TestUploadOutput(id=test_db.id)


async def update_test(
        test_id: int, update_data: TestUpdate, current_user: User, db_session: AsyncSession
) -> TestUploadOutput:
    test_db = await get_test_from_db(
        test_id=test_id, current_user=current_user, async_db_session=db_session
    )

    for key, value in update_data.model_dump(exclude_none=True).items():
        setattr(test_db, key, value)

    await db_session.commit()
    await db_session.refresh(test_db)

    return TestUploadOutput(id=test_db.id)


async def submit_test(
        test_id: int,
        payload: TestSubmitPayload,
        current_user: User,
        db_session: AsyncSession,
):
    test_db = await get_test_from_db(
        test_id=test_id, current_user=current_user, async_db_session=db_session
    )

    answered_test_content = fill_form_entries(
        test_content=test_db.content, payload_answers=payload.answers
    )

    data = {}
    for entry in answered_test_content.questions:
        value = (
                entry.user_answer
                or entry.llm_answer
                or entry.random_answer
                or None
        )

        data[f"entry.{entry.id}"] = value

    if test_db.url:
        formed_url: str = get_form_response_url(url=test_db.url)
        res = requests.post(url=formed_url, data=data, timeout=5)
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail='Error sending request to form')

        print(res.status_code)

    test_db.content = answered_test_content.model_dump()
    await db_session.commit()
    await db_session.refresh(test_db)
