# AGENTS.md

Rules for anyone, human or agent, changing this repository. `README.md` and
`docs/` describe the service; this file says how to work on it.

## What this project is

The identity service of Balatro in the browser: accounts, sign-in (email and
password, Google), and the tokens that the other services trust. Those are
BalatroWebAPI now, and later the leaderboards and lobbies. Its front end is
BalatroPortal, and the game (BalatroFrontEnd) shares the portal's session.
Its emails are sent by BalatroNotificationService: the codes go there as
`email.confirmation_code` messages (RabbitMQ). That message is a contract
documented in that repository's `docs/messages.md`; change both sides
together.

The repository's name has a typo ("Indentity"). It is the GitHub repository's
name and the folder name used on the server and by the deployment scripts, so
keep it there. Everything inside the code says "identity".

## Non-negotiable rules

1. **The token contract is public.** Other services check access tokens with
   the JWKS. Changing a claim (`iss`, `aud`, `sub`, `typ`, `name`), the
   algorithm (RS256) or the lifetimes changes them too: update
   `docs/integration.md`, BalatroWebAPI's `infrastructure/auth.py`, and the
   session code in BalatroPortal and BalatroFrontEnd together. `sub` is the
   account id, forever.
2. **Commit in the use case, before answering.** A use case that writes calls
   `unit_of_work.commit()` before it returns, and sends emails only after the
   commit. Never move the commit into a dependency's cleanup: it would run
   after the response is sent.
3. **Don't reveal accounts.** Forgot-password and resend answer the same for
   unknown emails. A login fails the same way for an unknown email and a wrong
   password, and takes as long (`verify_dummy`). Keep it that way.
4. **Secrets are single use and hashed.** Refresh tokens rotate, and reuse ends
   the session. Codes and OAuth states are used once and expire. Only hashes of
   refresh secrets are stored. Never log a password, a code (except with the
   `console` email backend, which is for development), or a token.
5. **Limit every guess.** A new way to check a secret gets an attempt limit
   (see `RedisConfirmationCodes`, `RedisLoginAttempts`).
6. **Schema changes are migrations.** Change the model, run
   `uv run alembic revision --autogenerate -m "..."`, read the result, and make
   sure `alembic check` passes against PostgreSQL (CI does). The app never
   calls `create_all`.

## Architecture

Clean architecture; [docs/architecture.md](docs/architecture.md) describes
the layers and the reasons behind the design.

```
domain  <-  application  <-  infrastructure, presentation  <-  bootstrap, main
```

- `app/domain`: entities and self-checking value objects; `DomainError` → 422.
- `app/application`: `use_cases/` (one class, one `execute`), `dtos/`
  (frozen dataclasses), `ports/` (`Protocol`s), `exceptions/` (`IdentityError`
  subclasses with a `code` and a default `message`).
- `app/infrastructure`: one adapter per port. No business decisions here.
- `app/presentation/api`: routes turn requests into DTOs and use case results
  into schemas. The status codes are in `exception_handler.STATUS`.
- `app/bootstrap/container.py`: the only place that picks adapters.

`tests/test_architecture.py` enforces the import rules. Fix the code, not the
test.

## Conventions

- Errors are problem details with a stable `code`. A new error is a new
  `IdentityError` subclass with its own `code`, given a status in `STATUS` and
  documented in `docs/api.md`.
- Request schemas only bound sizes. The rules (password length, name
  characters) belong to the domain's value objects.
- Settings are fields of `Settings` (environment variables of the same name),
  listed in `.env.example` and in the README.
- Style: ruff (line length 88), `mypy --strict`, absolute imports
  (`from app.… import …`), type hints everywhere.

## Adding things

- **An endpoint:** a use case (with unit-of-work commit if it writes), wired in
  `RequestContainer` (or `Container` if it needs no database), a route, a
  schema, and an API test in `tests/`.
- **A provider:** see "Adding a provider" in `docs/architecture.md`.
- **A column or table:** the model, a migration, the repository's mapping, and
  the entity.

## Commands

```
make install        # uv sync + pre-commit hook
make services       # PostgreSQL and Redis from ../BalatroFrontEnd/docker-compose.yml (the only compose file)
make run            # migrate, then serve on :8001
make check          # ruff format --check, ruff, mypy, pytest (CI runs this)
uv run alembic upgrade head | check | revision --autogenerate -m "..."
```

All of `make check` must pass before committing. Don't commit or push unless
asked. The branches are `dev` (work) and `main` (deployed by CI).
