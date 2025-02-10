FROM python:3.13-slim AS builder

WORKDIR /app
COPY poetry.lock pyproject.toml ./

RUN pip install --upgrade pip
RUN pip install poetry

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

COPY . .

FROM python:3.13-slim

WORKDIR /app
COPY --from=builder /app /app

CMD ["python3", "app/fetcher.py"]