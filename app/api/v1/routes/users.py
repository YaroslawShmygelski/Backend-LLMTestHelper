"""This module contains api endpoints for the Users connected logics"""
from fastapi import APIRouter, Depends

from app.database.mongodb_config import mongodb_connection

users_router = APIRouter()

@users_router.get("/user/{id}")
async def get_document(id: int, ):
    """Get document endpoint"""
    return "useer"
