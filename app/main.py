"""Application FastAPI main file"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import FastAPI, APIRouter
from sqlalchemy import text


from app.api.v1.routes import auth, document, users

from app.database.postgres_config import postgres_db_engine

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifecycle context manager for FastAPI application."""
    async with postgres_db_engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    await postgres_db_engine.dispose()


app = FastAPI(lifespan=lifespan)

api_v1_router = APIRouter(prefix="/api/v1")


api_v1_router.include_router(document.document_router, prefix="/documents")
api_v1_router.include_router(users.user_router, prefix="/users")
api_v1_router.include_router(auth.auth_router, prefix="/auth")

app.include_router(api_v1_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
