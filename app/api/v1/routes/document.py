"""This module contains api endpoints for the document connected logics"""

from fastapi import APIRouter

document_router = APIRouter()


@document_router.get("/document")
async def get_document():
    """Get document endpoint"""
    return "first document"
