# Stage 1: builder
FROM python:3.14-slim AS builder
WORKDIR /app
ENV UV_NO_CACHE=1
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync

# Stage 2: final, clean image
FROM python:3.14-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]