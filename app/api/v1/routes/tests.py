"""This module contains api endpoints for the document connected logics"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.tests import upload_google_doc_test
from app.database.postgres_config import get_async_postgres_session
from app.models.orm.user import User
from app.schemas.test import TestUploadOutput, GoogleDocsRequest

from app.services.users import get_user_from_token

tests_router = APIRouter(tags=["Tests"])


@tests_router.post("/add-test/google-docs", response_model=TestUploadOutput)
async def add_test_google_docs(
    link: GoogleDocsRequest,
    current_user: User = Depends(get_user_from_token),
    db_session: AsyncSession = Depends(get_async_postgres_session),
):

    result = await upload_google_doc_test(link, current_user, db_session)
    return result
