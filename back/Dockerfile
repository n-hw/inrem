# Build stage
FROM python:3.12-slim as requirements-stage

WORKDIR /tmp

RUN pip install poetry && poetry self add poetry-plugin-export

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry lock

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for asyncpg/psycopg2 compilation)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

# Expose port
EXPOSE 8000

# Command for development (reload enabled)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
