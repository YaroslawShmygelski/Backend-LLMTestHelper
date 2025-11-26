"""This module contains api endpoints for the document connected logics"""

import uuid

from fastapi import APIRouter, Depends, BackgroundTasks
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
    SubmitTestResponse,
    RunJobStatusResponse,
)

from app.services.users import get_user_from_token
from app.settings import JOBS_STORAGE
from app.utils.enums import JobStatus

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


@tests_router.post(
    "/submit/{test_id}", response_model=SubmitTestResponse, status_code=202
)
async def submit_test(
    test_id: int,
    payload: TestSubmitPayload,
    background_tasks: BackgroundTasks,  # TODO -> May add Celery for background tasks
    current_user: User = Depends(get_user_from_token),
) -> SubmitTestResponse:
    job_id = str(uuid.uuid4())

    # Simple storage as a dict TODO -> Add Redis for storing
    JOBS_STORAGE[job_id] = {
        "status": JobStatus.PENDING,
        "total_tests": payload.quantity,
        "processed_tests": 0,
        "results": [],
    }

    background_tasks.add_task(
        test_controllers.run_test_batch,
        job_id=job_id,
        test_id=test_id,
        payload=payload,
        current_user=current_user,
    )

    return SubmitTestResponse(
        job_id=job_id, message=f"Task accepted. Poll /status/{job_id} for updates."
    )


@tests_router.get(
    "/submit-status/{job_id}", response_model=RunJobStatusResponse, status_code=200
)
async def get_job_status(job_id: str) -> RunJobStatusResponse:
    result = await test_controllers.get_run_status(job_id)
    return result
