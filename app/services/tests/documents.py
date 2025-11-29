import io
import logging

import pdfplumber
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.orm.document import Document
from app.database.models.orm.document_embedding import DocumentEmbedding
from app.services.llm.embeddings import (
    get_document_chunks,
    generate_embeddings_for_chunks,
)
from app.settings import (
    ALLOWED_DOCUMENT_TYPES,
    MAX_DOCUMENT_SIZE,
    UPLOAD_DOCUMENT_JOBS_STORAGE,
    PDF_DOCUMENT_TYPE,
)
from app.utils.enums import JobStatus
from app.utils.exception_types import WrongRequestError

logger = logging.getLogger(__name__)


async def check_request_document(document: UploadFile) -> bytes:
    if document.content_type not in ALLOWED_DOCUMENT_TYPES:
        raise WrongRequestError(
            message="Unsupported file type. Only TXT and PDF allowed."
        )
    document_content = await document.read()
    if len(document_content) > MAX_DOCUMENT_SIZE:
        raise WrongRequestError(message="File too large. Max 5 MB allowed.")

    logger.info(f"Document content length: {len(document_content)}")
    return document_content


async def extract_text_from_document(document_content: bytes, content_type: str) -> str:
    if content_type == PDF_DOCUMENT_TYPE:
        try:
            with pdfplumber.open(io.BytesIO(document_content)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            return ""
    else:
        text = document_content.decode("utf-8")
    return text.strip()

async def save_document_embeddings(
    db_session: AsyncSession,
    document_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
):
    db_embeddings = [
        DocumentEmbedding(
            document_id=document_id,
            chunk_index=i,
            chunk_text=chunk,
            embedding=embedding,
        )
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]
    db_session.add_all(db_embeddings)
    await db_session.commit()


async def process_document_job(
    job_id: str,
    test_id: int,
    document: UploadFile,
    scope: str,
    db_session: AsyncSession,
):
    UPLOAD_DOCUMENT_JOBS_STORAGE[job_id]["status"] = JobStatus.PROCESSING

    try:
        document_content = await check_request_document(document=document)
        text = await extract_text_from_document(document_content, document.content_type)
        chunks = await get_document_chunks(
            text=text, storage=UPLOAD_DOCUMENT_JOBS_STORAGE, job_id=job_id
        )
        embeddings = await generate_embeddings_for_chunks(chunks)

        document_db = Document(
            file_name=document.filename,
            original_file_name=document.filename,
            file_type=document.content_type,
            size_bytes=len(document_content),
            test_id=test_id,
            scope=scope,
        )
        db_session.add(document_db)
        await db_session.flush()

        await save_document_embeddings(db_session, document_db.id, chunks, embeddings)

        return document_db.id, len(chunks)

    except Exception as e:
        UPLOAD_DOCUMENT_JOBS_STORAGE[job_id]["status"] = JobStatus.FAILED
        UPLOAD_DOCUMENT_JOBS_STORAGE[job_id]["error"] = str(e)
        raise WrongRequestError(message="Error while uploading your document")
