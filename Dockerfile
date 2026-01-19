FROM python:3.12-slim

WORKDIR /app

ENV UV_SYSTEM_PYTHON=1

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "quiz_engine.app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
