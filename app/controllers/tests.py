from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm.user import User
from app.parsers.google_form import get_form_submit_request
from app.schemas.test import TestUploadOutput, GoogleDocsRequest


async def upload_google_doc_test(
    link: GoogleDocsRequest, current_user: User, db_session: AsyncSession
) -> TestUploadOutput:
    print(link)
    parsed_form_data=get_form_submit_request(url=link.link, output="return", with_comment=True, only_required=False)
    print(parsed_form_data)
    return TestUploadOutput(id=1, status_code=201)
