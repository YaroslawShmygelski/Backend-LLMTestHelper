"""Application FastAPI main file"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.routes.document import document_router
from app.api.v1.routes.users import user_router
from app.database.postgres_config import postgres_db_engine

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with postgres_db_engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    await postgres_db_engine.dispose()


app = FastAPI(lifespan=lifespan)


app.include_router(document_router)  # /documents
app.include_router(user_router)  # /users


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
