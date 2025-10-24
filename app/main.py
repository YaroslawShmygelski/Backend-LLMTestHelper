"""Application FastAPI main file"""
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import FastAPI
from app.api.v1.routes.document import document_router
from app.database.mongodb_config import mongodb_connection


load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongodb_connection.connect()
    try:
        yield
    finally:
        await mongodb_connection.close()

app = FastAPI(lifespan=lifespan)


app.include_router(document_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
