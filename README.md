# LLMTestHelper

It is a backend service of **LLMTestHelper** designed to help users complete knowledge or skill-based tests using input materials such as Google Docs, PDF files, and other document types. It leverages modern Python technologies and asynchronous processing to deliver fast, reliable, and scalable performance.

## Tech Stack

- **Python 3.12+**
- **FastAPI** — modern, async web framework
- **SQLAlchemy 2.0** — ORM and database toolkit
- **Alembic** — database migrations
- **Pydantic** — data validation and settings management
- **PostgreSQL** (with **pgvector** extension) — relational and vector database
- **uv** — package and environment manager for Python
- **Docker & Docker Compose** — containerization

---

## Getting Started (Local Development)

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

### 4. Configure environment variables

Create a `.env` file in the project root and fill it with data mentioned in `.env.dist`.

### 5. Apply database migrations

```bash
alembic upgrade head

```

### 6. Run the FastAPI server

```bash
uv run uvicorn app.main:app --reload

```

The server will start at:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Docker Support (Makefile)

This project uses **Docker Compose** for deployment and local testing. A `Makefile` is provided to simplify common commands and handle environment file configuration automatically.

### Prerequisites

* Docker & Docker Compose
* Make (pre-installed on Linux/macOS; requires WSL or Make for Windows)

### Configuration

Create a `.env.compose` file in the project root. You can copy `.env.dist` as a template, but ensure the database host is set to the service name defined in Docker Compose:

```ini
# Example for .env.compose
POSTGRES_HOST=db
POSTGRES_USER=app_user
POSTGRES_PASSWORD=secret_password
POSTGRES_DB=app_db

```

### Commands

| Command | Description |
| --- | --- |
| **`make up`** | Builds images and starts all services (DB, Migrator, Backend) in detached mode. |
| **`make down`** | Stops and removes containers and networks. |
| **`make logs`** | Follows the logs of all running containers. |
| **`make clean-up`** | **WARNING:** Stops containers and **removes volumes** (database data), then restarts. Use this for a fresh start or if the DB schema is corrupted. |

#### Usage Example:

```bash
# Start the project
make up

# Check logs if something goes wrong
make logs

# Stop the project
make down

```

---

## License

This project is licensed under the MIT License. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

## Author

**Yaroslaw Shmygelski**
[GitHub](https://github.com/YaroslawShmygelski)