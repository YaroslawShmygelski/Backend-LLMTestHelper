"""Application FastAPI main file"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import auth, tests, users

from app.database.postgres_config import postgres_db_engine
from app.middlewares import LoggingMiddleware
from app.settings import custom_openapi
from app.utils.logging import setup_logging

load_dotenv()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifecycle context manager for FastAPI application."""
    async with postgres_db_engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    await postgres_db_engine.dispose()


setup_logging()
app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

# Change OpenApi schema to Make Bearer Authorization
app.openapi = lambda: custom_openapi(app)

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth.auth_router, prefix="/auth")
api_v1_router.include_router(tests.tests_router, prefix="/tests")
api_v1_router.include_router(users.user_router, prefix="/users")


app.include_router(api_v1_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
