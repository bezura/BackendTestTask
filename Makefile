.PHONY: lint format typecheck check

lint:
	ruff check .

format:
	black .
	ruff format .
	ruff check . --fix

typecheck:
	mypy app tests

check: format lint typecheck
