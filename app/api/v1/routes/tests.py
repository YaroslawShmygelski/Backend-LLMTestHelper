"""This module contains api endpoints for the document connected logics"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import tests as test_controllers
from app.database.postgres_config import get_async_postgres_session
from app.models.orm.user import User
from app.schemas.test import (
    TestUploadOutput,
    GoogleDocsRequest,
    TestUpdate,
    TestSubmittedOutput,
    TestSubmitPayload,
)

from app.services.users import get_user_from_token

tests_router = APIRouter(tags=["Tests"])


@tests_router.post("/google-docs", response_model=TestUploadOutput, status_code=201)
async def add_test_google_docs(
    link: GoogleDocsRequest,
    current_user: User = Depends(get_user_from_token),
    async_db_session: AsyncSession = Depends(get_async_postgres_session),
):

    result = await test_controllers.upload_google_doc_test(
        link, current_user, async_db_session
    )
    return result


@tests_router.patch("/{test_id}", response_model=TestUploadOutput, status_code=200)
async def update_test(
    test_id: int,
    update_data: TestUpdate,
    current_user: User = Depends(get_user_from_token),
    async_db_session: AsyncSession = Depends(get_async_postgres_session),
):
    result = await test_controllers.update_test(
        test_id, update_data, current_user, async_db_session
    )
    return result


@tests_router.post("/submit/{test_id}", response_model=None, status_code=200)
async def submit_test(
    test_id: int,
    current_user: User = Depends(get_user_from_token),
    async_db_session: AsyncSession = Depends(get_async_postgres_session),
):
    result = await test_controllers.submit_test(test_id, current_user, async_db_session)
    return result
