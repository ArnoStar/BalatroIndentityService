# Balatro Identity Service

Accounts and sign-in for Balatro in the browser. Players sign in with an email
and a password, or with Google. The service hands out:

- an **access token**: an RS256 JWT, valid 15 minutes. The other services
  (BalatroWebAPI, and later the leaderboards and lobbies) check it themselves
  with the public keys at `/.well-known/jwks.json`. They never call this
  service per request.
- a **refresh token**: opaque and single use, valid 30 days, exchanged at
  `POST /auth/refresh` for a new pair.

```
 browser ── portal (/)  ──► identity  /auth/*, /oauth/*        sign in, refresh
    │                           │
    │                           └─ /.well-known/jwks.json ◄─┐  public keys
    └──── game (/play/) ──► api  Authorization: Bearer <jwt> ─┘  (cached by the API)
```

It is a FastAPI application in clean architecture, with PostgreSQL for the
accounts and Redis for everything short-lived: sessions, codes, login
throttling and sign-in states.

| | |
|---|---|
| [docs/api.md](docs/api.md) | every endpoint, its body and its errors |
| [docs/integration.md](docs/integration.md) | how a service checks the tokens; how a front end signs in and refreshes |
| [docs/architecture.md](docs/architecture.md) | the layers, the data, the security decisions |
| [AGENTS.md](AGENTS.md) | the rules for changing this repository |

## Run it

You need Python 3.13, [uv](https://docs.astral.sh/uv/) and Docker (for
PostgreSQL and Redis).

```
make install          # dependencies and the pre-commit hook
make services         # PostgreSQL (localhost:55432) and Redis (:56379) in Docker
make run              # migrates, then serves http://localhost:8001 (docs at /docs)
```

The services come from the game's single compose file,
`../BalatroFrontEnd/docker-compose.yml`. It runs the whole site (portal, game,
API, this service, and its PostgreSQL and Redis), and optionally Mailpit and
RabbitMQ. `make compose` runs this service from it too, in Docker, and
`make decompose` stops this service's containers. Their data stays in the
volumes.

With the defaults, emails are written to the log (`EMAIL_BACKEND=console`).
The 6-digit codes to confirm an email or reset a password are printed there.
To see real emails, run `make services-mail` and set `EMAIL_BACKEND=smtp`,
`SMTP_HOST=localhost`, `SMTP_PORT=1025` and `SMTP_SECURITY=none`. They then
arrive in Mailpit's inbox at http://localhost:8025.

The JWT signing key is created in `keys/jwt_private.pem` on the first start.

## Configuration

Settings are environment variables, or lines of a `.env` file.
[.env.example](.env.example) lists them all with their defaults:

| Variable | Default | |
|---|---|---|
| `PUBLIC_URL` | `http://localhost:8001` | the service's public URL; it becomes the tokens' issuer (`iss`), and the API must expect the same value |
| `CORS_ORIGINS` | the dev servers | browser origins allowed to call the service, comma separated |
| `DATABASE_URL` | `make services`' PostgreSQL (:55432) | `postgresql+asyncpg://...` |
| `REDIS_URL` | `redis://localhost:56379/0` | |
| `JWT_PRIVATE_KEY` / `JWT_PRIVATE_KEY_FILE` | `keys/jwt_private.pem` | the RS256 key, as PEM text or a file (created if missing while `JWT_GENERATE_KEY=true`) |
| `JWT_AUDIENCE` | `balatro` | the tokens' `aud` |
| `ACCESS_TOKEN_LIFETIME_MINUTES` / `REFRESH_TOKEN_LIFETIME_DAYS` | 15 / 30 | |
| `EMAIL_BACKEND` | `console` | `console`, `smtp` (with `SMTP_*`) or `rabbitmq` (for a separate mail worker) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | unset | Google sign-in is on when both are set |
| `OAUTH_REDIRECT_URIS` | the portal's dev URLs | the pages Google may send the browser back to (the portal's `/auth/callback`) |

### Google sign-in

The code is all there (here and in the portal). It turns on when the service
has a Google client id and secret.

1. At https://console.cloud.google.com, create a project, or pick one.
2. *APIs & Services → OAuth consent screen*: choose *External* and fill in the
   app's name and your email. The scopes are `openid`, `email` and `profile`;
   they need no review. While the app is in *Testing*, add the Google accounts
   that may sign in under *Test users*. *Publish* it to open it to everyone.
3. *APIs & Services → Credentials → Create credentials → OAuth client ID*, of
   type *Web application*. Under *Authorized redirect URIs*, add the portal's
   callback page for each place the site runs, exactly as in
   `OAUTH_REDIRECT_URIS`:
   - `http://localhost:5174/auth/callback`: development, the portal's dev server;
   - `http://localhost:8087/auth/callback`: the Docker stack;
   - `https://<your domain>/auth/callback`: the server (`PUBLIC_URL` +
     `/auth/callback`; the compose file sets `OAUTH_REDIRECT_URIS` to it).
4. Give the service the client id and secret:
   - for `make run`: `GOOGLE_CLIENT_ID=...` and `GOOGLE_CLIENT_SECRET=...` in
     this repository's `.env`;
   - for the Docker stack and the server: the same two lines in
     `BalatroFrontEnd/.env` (on the server, `/opt/balatro/BalatroFrontEnd/.env`),
     then restart `identity`.

`GET /oauth/providers` then lists `google`. The portal shows *Continue with
Google* on its sign-in and registration pages, and *Link Google* on the
account page.

What happens when someone signs in with Google is in
[docs/api.md](docs/api.md#sign-in-with-a-provider): an existing link signs in,
a verified email matching an account links it, otherwise a new account named
after the Google profile is created. *Link Google*, on the account page, links
any Google account to the signed-in player.

### Email

- `smtp`: set `SMTP_HOST`, `SMTP_PORT` and `SMTP_SECURITY` (`starttls` on 587,
  `ssl` on 465, or `none`), `SMTP_USERNAME`, `SMTP_PASSWORD` and `EMAIL_FROM`.
- `rabbitmq`: publishes `{"email", "subject", "body"}` to the `notifications`
  exchange with routing key `email.send`, bound to the `email_worker_queue`
  queue. Something else must deliver the messages. The compose file's
  `rabbitmq` service (`--profile rabbitmq`) provides the broker; the identity
  container is already pointed at it.

## Checks

```
make check            # ruff format --check, ruff, mypy --strict, pytest
```

The tests (`tests/`) run the real application against SQLite, fakeredis, an
outbox and a fake Google, so they need no services. CI also runs the migration
against PostgreSQL and checks with `alembic check` that it matches the models.

## Database migrations

```
uv run alembic upgrade head                         # (make migrate)
uv run alembic revision --autogenerate -m "..."     # after changing a model; read the result
```

The Docker image migrates on start (`MIGRATE_ON_START=1`).

## Deployment

`.github/workflows/ci-cd.yml` checks every push and pull request on `main`
and `dev`. A push to `main` deploys like the other repositories:
`.github/deploy.sh` copies the code to `DEPLOY_PATH/BalatroIndentityService`
on the server, and BalatroFrontEnd's `docker-compose.yml` rebuilds the
`identity` service. It uses the same `DEPLOY_*` secrets as BalatroWebAPI; see
BalatroFrontEnd's README for the server's setup.

On the server, the settings go in `/opt/balatro/BalatroFrontEnd/.env`, which
deployments keep:

```
PUBLIC_URL=https://example.com
IDENTITY_DB_PASSWORD=<a long random password>
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.example.com
SMTP_USERNAME=...
SMTP_PASSWORD=...
EMAIL_FROM=Balatro <no-reply@example.com>
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

The signing key lives in the `identity-data` volume. Deleting that volume
signs everyone out of the game within 15 minutes, when their access tokens
expire. Refresh tokens are kept in Redis and survive a new key.

## What changed from the first version

The first version (BelFlix's) had problems that made it unusable or unsafe:

- The migration was empty, so the tables existed only through `create_all`.
- The database commit ran after the response was sent.
- Nothing read the RabbitMQ email queue, so no account could be confirmed.
- Refresh tokens could be replayed and never revoked.
- Confirmation codes could be brute-forced.
- Passwords over 72 bytes caused a 500.
- The OAuth callback returned tokens to Google's redirect target instead of
  the front end.
- The compose file mounted RabbitMQ config files that didn't exist.

[docs/architecture.md](docs/architecture.md#decisions) gives the reasons
behind each fix.
