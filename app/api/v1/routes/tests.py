"""This module contains api endpoints for the document connected logics"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import tests as test_controllers
from app.database.postgres_config import get_async_postgres_session
from app.models.orm.user import User
from app.schemas.test import (
    TestResponse,
    GoogleDocsRequest,
    TestUpdate,
    TestSubmitPayload,
    TestGetResponse,
    TestRunResponse,
)

from app.services.users import get_user_from_token

tests_router = APIRouter(tags=["Tests"])


@tests_router.post("/google-docs", response_model=TestResponse, status_code=201)
async def add_test_google_docs(
    payload: GoogleDocsRequest,
    current_user: User = Depends(get_user_from_token),
    async_db_session: AsyncSession = Depends(get_async_postgres_session),
):
    result = await test_controllers.upload_google_doc_test(
        payload, current_user, async_db_session
    )
    return result


@tests_router.get("/{test_id}", response_model=TestGetResponse, status_code=200)
async def get_test(
    test_id: int,
    current_user: User = Depends(get_user_from_token),
    async_db_session: AsyncSession = Depends(get_async_postgres_session),
) -> TestGetResponse:
    result = await test_controllers.get_test(
        test_id=test_id, current_user=current_user, db_session=async_db_session
    )
    return result


@tests_router.get(
    "/test-runs/{run_id}", response_model=TestRunResponse, status_code=200
)
async def get_test_run(
    run_id: int,
    current_user: User = Depends(get_user_from_token),
    async_db_session: AsyncSession = Depends(get_async_postgres_session),
):
    result = await test_controllers.get_test_run(
        run_id=run_id, current_user=current_user, db_session=async_db_session
    )
    return result


@tests_router.patch("/{test_id}", response_model=TestResponse, status_code=200)
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


@tests_router.post("/submit/{test_id}", response_model=TestResponse, status_code=200)
async def submit_test(
    test_id: int,
    payload: TestSubmitPayload,
    current_user: User = Depends(get_user_from_token),
    async_db_session: AsyncSession = Depends(get_async_postgres_session),
) -> TestResponse:
    result = await test_controllers.submit_test(
        test_id=test_id,
        payload=payload,
        current_user=current_user,
        db_session=async_db_session,
    )
    return result
