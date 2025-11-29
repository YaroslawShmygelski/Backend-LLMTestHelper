from fastapi import UploadFile
from pydantic import BaseModel


class UploadDocumentRequest(BaseModel):
    test_id: int
    document: UploadFile
