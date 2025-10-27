"""This module contains api endpoints for the document connected logics"""

from fastapi import APIRouter

document_router = APIRouter(prefix="/documents", tags=["Documents"])


@document_router.get("/document")
async def get_document():
    """Get document endpoint"""
    return "first document"
