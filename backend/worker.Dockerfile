FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==0.13.7
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"
COPY backend/ ./backend/
COPY alembic.ini ./

CMD ["python", "-m", "backend.worker"]
