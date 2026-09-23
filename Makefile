install:
	uv sync
	uv run pre-commit install

run:
	uv run uvicorn app.main:app --reload

format:
	uv run ruff format .
	uv run ruff check . --fix

lint:
	uv run ruff check . --fix

typecheck:
	uv run mypy .

tests:
	uv run pytest

check:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy .
	uv run pytest