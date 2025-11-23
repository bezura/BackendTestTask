FROM python:3.13-slim

WORKDIR /app

# uv installs itself
RUN pip install uv

COPY pyproject.toml .
COPY uv.lock* ./
RUN uv sync

COPY . .

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
