from fastapi import APIRouter

document_router=APIRouter()

@document_router.get("/document")
async def get_document():
    return "first document"
