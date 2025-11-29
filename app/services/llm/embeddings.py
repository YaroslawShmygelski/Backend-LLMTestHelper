from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.settings import CHUNK_SIZE, CHUNK_OVERLAP


async def get_document_chunks(text: str, storage: dict, job_id: str) -> list:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(text)
    storage[job_id]["total_chunks"] = len(chunks)
    return chunks