# BalatroIndentityService: `make` lists the commands.
#
# Alone:        make install && make services && make run   (http://localhost:8001, docs at /docs)
# Everything:   make dev in ../BalatroFrontEnd (the whole site, each part from its repository)
.DEFAULT_GOAL := help
.PHONY: help install services services-mail run migrate format check tests docker compose decompose

# the whole game's compose file (BalatroFrontEnd), which has this service and its
# PostgreSQL, Redis, Mailpit and RabbitMQ
STACK := ../BalatroFrontEnd/docker-compose.yml

help:
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-14s %s\n", $$1, $$2}'

install:            ## dependencies and the pre-commit hook
	uv sync
	uv run pre-commit install

services:           ## PostgreSQL (:55432) and Redis (:56379) in Docker, for `make run`
	docker compose -f $(STACK) up -d identity-db identity-redis

services-mail:      ## the same, and Mailpit (inbox at http://localhost:8025, SMTP :1025)
	docker compose -f $(STACK) --profile mail up -d identity-db identity-redis mailpit

run: migrate        ## the service on http://localhost:8001 (reloads on changes)
	uv run uvicorn app.main:app --reload --port 8001

migrate:            ## bring the database up to date
	uv run alembic upgrade head

format:             ## format and fix what can be fixed
	uv run ruff format .
	uv run ruff check . --fix

check:              ## what CI runs (ruff format, ruff, mypy, pytest)
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy
	uv run pytest

tests:              ## the tests
	uv run pytest

docker: compose     ## (the same as compose)

compose:            ## this service in Docker too (http://localhost:8001)
	docker compose -f $(STACK) up -d --build identity

decompose:          ## stop this service's containers (their data stays in the volumes)
	docker compose -f $(STACK) rm -s -f identity identity-db identity-redis mailpit
