import asyncio
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.llm.llm_config import embeddings_model
from app.settings import CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_DIM

logger = logging.getLogger(__name__)


async def get_document_chunks(text: str, storage: dict, job_id: str) -> list:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(text)
    storage[job_id]["total_chunks"] = len(chunks)
    logger.info(
        "Document was splited to chunks", extra={"job_id": job_id, "chunks": chunks}
    )
    return chunks


async def generate_embeddings_for_chunks(chunks: list[str]) -> list[list[float]]:
    loop = asyncio.get_event_loop()
    embeddings = await loop.run_in_executor(
        None, lambda: embeddings_model.embed_documents(chunks, output_dimensionality=1536)
    )
    if chunks:
        dim = len(embeddings[0])
        if dim != EMBEDDING_DIM:
            raise ValueError(f"Dimension mismatch expected: {EMBEDDING_DIM} received: {dim}")
    logger.info("Generated embeddings for chunks", extra={"embeddings": len(embeddings)})
    return embeddings
