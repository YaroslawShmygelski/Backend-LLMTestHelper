# LLMTestHelper 
It is a backend service of **LLMTestHelper** designed to help users complete knowledge or skill-based tests using input materials such as Google Docs, PDF files, and other document types. It leverages modern Python technologies and asynchronous processing to deliver fast, reliable, and scalable performance.

## Tech Stack

- Python 3.12+
- FastAPI — modern, async web framework  
- SQLAlchemy 2.0 — ORM and database toolkit  
- Alembic — database migrations  
- Pydantic — data validation and settings management  
- PostgreSQL — relational database  
- uv — package and environment manager for Python

## Getting Started

### 1. Clone the repository
```bash
git clone git@github.com:YaroslawShmygelski/Backend-LLMTestHelper.git
cd Backend-LLMTestHelper
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Activate the virtual environment

```bash
source .venv/bin/activate
```

### 4. (Optional) Resynchronize dependencies

```bash
uv sync
```

### 5. Configure environment variables

Create a `.env` file in the project root and fill it with data mentioned in `.env.dist`

### 6. Apply database migrations

```bash
alembic upgrade head
```

### 7. Run the FastAPI server

```bash
uv run uvicorn app.main:app --reload
```

The server will start at:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

**Yaroslaw Shmygelski**
[GitHub](https://github.com/YaroslawShmygelski)
