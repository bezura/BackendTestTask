#!/bin/sh

set -e

# Применяем миграции
uv run alembic upgrade head

# Запускаем приложение
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
