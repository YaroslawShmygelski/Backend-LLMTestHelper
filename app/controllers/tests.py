from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm.user import User
from app.parsers.google_form import parse_form_entries
from app.schemas.test import TestUploadOutput, GoogleDocsRequest, TestContent
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

    print(test_db.id)

    return TestUploadOutput(id=1, status_code=201)
