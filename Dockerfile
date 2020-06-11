FROM python:3.8-slim as base
WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates git \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM base as builder
COPY pyproject.toml .
COPY poetry.lock .
RUN pip install poetry --no-cache-dir
RUN poetry export -f requirements.txt -o /requirements.txt


FROM base
COPY . .
COPY --from=builder /requirements.txt requirements.txt
RUN rm -rf poetry.lock pyproject.toml
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
