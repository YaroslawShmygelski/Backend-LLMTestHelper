import logging
import uuid

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.orm.test_run import TestRun
from app.database.models.orm.user import User
from app.parsers.google_form import parse_google_form
from app.schemas.tests.test import (
    TestResponse,
    GoogleDocsRequest,
    TestQuestions,
    TestUpdate,
    TestGetResponse,
    TestRunResponse,
    RunJobStatusResponse,
    SubmitTestResponse,
    RunsOfTest,
    RunsOfTestResponse,
)
from app.services.tests.tests import (
    normalize_parsed_data,
    save_test_in_db,
    get_test_from_db,
    run_background_tests,
    get_runs_of_test_db,
)
from app.services.tests.documents import process_document_job
from app.settings import TEST_RUNS_JOBS_STORAGE, UPLOAD_DOCUMENT_JOBS_STORAGE
from app.utils.enums import JobStatus
from app.utils.exception_types import NotFoundError
from app.utils.logging import correlation_id

logger = logging.getLogger(__name__)


async def upload_google_doc_test(
    payload: GoogleDocsRequest, current_user: User, async_db_session: AsyncSession
) -> TestResponse:
    # 1. Logowanie — kto i co robi
    logger.info(
        "google_doc_import",
        extra={"user_id": current_user.id, "test_url": payload.test_url},
    )
    # 2. Wywołanie parsera — pobranie pytań z Google Form
    parsed_data = parse_google_form(url=payload.test_url, only_required=False)
    # 3. Wywołanie serwisu — normalizacja danych
    test_content: TestQuestions = normalize_parsed_data(parsed_data)
    # 4. Wywołanie serwisu — zapis do bazy danych
    test_db = await save_test_in_db(
        test_content=test_content,
        test_url=payload.test_url,
        title=payload.title,
        current_user=current_user,
        async_db_session=async_db_session,
    )
    # 5. Formatowanie odpowiedzi
    return TestResponse(test_id=test_db.id)


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
        title=test_db.title,
        is_submitted=test_db.is_submitted,
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

    return TestResponse(test_id=test_db.id)


async def start_test_batch(test_id, payload, current_user, background_tasks):
    job_id = str(uuid.uuid4())

    TEST_RUNS_JOBS_STORAGE[job_id] = {
        "status": JobStatus.PENDING,
        "total_tests": payload.quantity,
        "processed_tests": 0,
        "results": [],
    }

    background_tasks.add_task(
        run_background_tests,
        job_id=job_id,
        test_id=test_id,
        payload=payload,
        current_user=current_user,
    )

    return SubmitTestResponse(
        job_id=job_id, message=f"Task accepted. Poll /status/{job_id} for updates."
    )


async def get_run_status(job_id: str):
    job = TEST_RUNS_JOBS_STORAGE.get(job_id)
    if not job:
        raise NotFoundError(message="Test run Job not found")

    current_status = job["status"]
    response = RunJobStatusResponse(
        job_id=job_id,
        status=job["status"],
        processed_runs_count=job["processed_tests"],
        total_runs=job["total_tests"],
        results=None,
    )

    if current_status == JobStatus.COMPLETED:
        job_results = job["results"]
        response.results = job_results

    return response


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


async def get_runs_of_test(
    test_id: int, current_user: User, async_db_session: AsyncSession
) -> RunsOfTestResponse:
    test_runs_db = await get_runs_of_test_db(
        test_id=test_id, current_user=current_user, db_session=async_db_session
    )
    result = [
        RunsOfTest(
            run_id=test_run.id,
            test_id=test_run.test_id,
            user_id=test_run.user_id,
            job_id=test_run.job_id,
            submitted_date=test_run.submitted_date,
            llm_model=test_run.llm_model,
        )
        for test_run in test_runs_db
    ]

    return RunsOfTestResponse(test_runs=result)


async def upload_document(
    document: UploadFile,
    test_id: int,
    user_id: int,
    background_tasks: BackgroundTasks,
    async_db_session: AsyncSession,
):

    job_id = str(uuid.uuid4())
    UPLOAD_DOCUMENT_JOBS_STORAGE[job_id] = {
        "status": JobStatus.PENDING,
        "file_name": document.filename,
        "processed_chunks": 0,
        "total_chunks": 0,
        "error": None,
    }

    background_tasks.add_task(
        process_document_job,
        job_id=job_id,
        user_id=user_id,
        test_id=test_id,
        document=document,
        db_session=async_db_session,
        scope="test",
    )
    return {"job_id": job_id, "status": JobStatus.PROCESSING}
