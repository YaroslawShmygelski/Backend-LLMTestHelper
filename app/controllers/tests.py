from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.orm.test import Test
from app.models.orm.user import User
from app.parsers.google_form import parse_form_entries
from app.schemas.test import TestUploadOutput, GoogleDocsRequest, TestContent, TestUpdate
from app.services.tests import normalize_test_data, store_test_in_db


async def upload_google_doc_test(
    link: GoogleDocsRequest, current_user: User, async_db_session: AsyncSession
) -> TestUploadOutput:

    parsed_data = parse_form_entries(url=link.link, only_required=False)

    test_content: TestContent = normalize_test_data(parsed_data)

    test_db = await store_test_in_db(
        test_content=test_content,
        current_user=current_user,
        async_db_session=async_db_session,
    )

    return TestUploadOutput(id=test_db.id)


async def update_test(test_id: int, update_data: TestUpdate, current_user: User, db_session: AsyncSession):
    result = await db_session.execute(
        Select(Test).where(Test.id == test_id, Test.user_id == current_user.id)
    )
    test_db=result.scalar_one_or_none()

    if not test_db:
        raise HTTPException(status_code=404, detail="Test not found")


    for key, value in update_data.model_dump(exclude_none=True).items():
        setattr(test_db, key, value)

    await db_session.commit()
    await db_session.refresh(test_db)

    return TestUploadOutput(id=test_db.id)

