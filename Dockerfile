FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir \
    fastapi>=0.110 \
    "uvicorn[standard]>=0.29" \
    sqlalchemy>=2.0 \
    pymysql>=1.1 \
    jinja2>=3.1 \
    python-dotenv>=1.0

COPY app ./app
COPY pyproject.toml ./pyproject.toml

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
