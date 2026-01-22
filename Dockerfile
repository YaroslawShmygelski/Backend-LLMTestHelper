FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Make UV use Image python version to avoid 3.14 issues
ENV UV_PYTHON=/usr/local/bin/python \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

# Create clean runtime image
FROM python:3.13-slim-bookworm AS runtime

RUN groupadd -r appuser && useradd -r -g appuser appuser

ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app
# Copy clean virtual envirment from builder phase
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]