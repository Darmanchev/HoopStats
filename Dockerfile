FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv==0.11.31

COPY pyproject.toml uv.lock ./

ENV UV_PROJECT_ENVIRONMENT=/opt/venv

RUN uv sync --frozen --no-dev --no-install-project

ENV PATH="/opt/venv/bin:$PATH"

COPY backend/app ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
