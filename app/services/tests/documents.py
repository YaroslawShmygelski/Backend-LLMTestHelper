import io

import pdfplumber
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.orm.document import Document
from app.database.models.orm.user import User
from app.settings import ALLOWED_DOCUMENT_TYPES, MAX_DOCUMENT_SIZE, UPLOAD_DOCUMENT_JOBS_STORAGE, PDF_DOCUMENT_TYPE
from app.utils.enums import JobStatus
from app.utils.exception_types import WrongRequestError



async def check_request_document(document: UploadFile) -> bytes:
    if document.content_type not in ALLOWED_DOCUMENT_TYPES:
        raise WrongRequestError(message="Unsupported file type. Only TXT and PDF allowed.")
    document_content = await document.read()
    if len(document_content) > MAX_DOCUMENT_SIZE:
        raise WrongRequestError(message="File too large. Max 5 MB allowed.")

    return document_content

async def process_document_job(job_id: str, test_id: int, document: UploadFile, document_content: bytes, scope: str,
                               current_user: User, db_session: AsyncSession) -> None:
    UPLOAD_DOCUMENT_JOBS_STORAGE[job_id]["status"] = JobStatus.PROCESSING

    try:
        if document.content_type == PDF_DOCUMENT_TYPE:
            with pdfplumber.open(io.BytesIO(document_content)) as pdf:
                text = "\n".join(page.extract_text() for page in pdf.pages)
        else:
            text = document_content.decode("utf-8")

        document_db = Document(
            file_name=document.filename,
            original_file_name=document.filename,
            file_type=document.content_type,
            size_bytes=len(document_content),
            test_id=test_id,
            scope=scope
        )
        db_session.add(document_db)
        await db_session.commit()

        chunks = get_document_chunks(text=text, storage=UPLOAD_DOCUMENT_JOBS_STORAGE, job_id=job_id)

    except Exception as e:
        UPLOAD_DOCUMENT_JOBS_STORAGE[job_id]["status"] = JobStatus.FAILED
        UPLOAD_DOCUMENT_JOBS_STORAGE[job_id]["error"] = str(e)
        raise WrongRequestError(message="Error while uploading your document")
