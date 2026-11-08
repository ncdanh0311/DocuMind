FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==0.13.7
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --only-group backend
ENV PATH="/app/.venv/bin:$PATH"
COPY backend/ ./backend/
COPY alembic.ini ./
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
