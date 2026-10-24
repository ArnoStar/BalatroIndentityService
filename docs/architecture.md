# Architecture

## Layers

```
domain  <-  application  <-  infrastructure, presentation  <-  bootstrap, main
```

| Layer | Folder | What it holds | May import |
|---|---|---|---|
| Domain | `app/domain` | entities (`User`, `PasswordCredential`, `OAuthAccount`), value objects that check themselves (`Email`, `Password`, `DisplayName`, `PasswordHash`, `OAuthProvider`), `DomainError`s | the standard library |
| Application | `app/application` | one class per use case (`use_cases/`), their DTOs (`dtos/`), the ports they need (`ports/`, `typing.Protocol`), `IdentityError`s with a stable `code` | domain |
| Infrastructure | `app/infrastructure` | the adapters: SQLAlchemy repositories and unit of work, Redis stores, bcrypt, the JWT issuer and key, email senders, the Google client, settings | domain, application |
| Presentation | `app/presentation/api` | FastAPI routes, pydantic schemas, dependencies, errors mapped to problem details | domain, application, bootstrap |
| Composition | `app/bootstrap/container.py`, `app/main.py` | builds the adapters and the use cases; makes the app | everything |

`tests/test_architecture.py` enforces these rules. The domain and application
layers also may not import FastAPI, pydantic, SQLAlchemy, Redis, httpx or
PyJWT.

`Container` is built once in the app's lifespan. It holds the engine, the
Redis and HTTP clients, the signing key, the email sender, and the use cases
that need no database. For each request, `container.request(session)` builds
a `RequestContainer` with the repositories and use cases on that request's
database session.

## Data

PostgreSQL (`alembic/versions`):

```
users                 id (uuid), email (unique, lower case), display_name,
                      email_verified_at, created_at, updated_at
password_credentials  user_id → users (ON DELETE CASCADE), password_hash (bcrypt)
oauth_accounts        id, user_id → users (CASCADE), provider, provider_user_id,
                      unique (provider, provider_user_id), unique (user_id, provider)
```

Redis (all keys expire):

| Key | Value | Lifetime |
|---|---|---|
| `session:<sid>` | hash: `user_id`, `secret` (SHA-256 of the refresh token's secret) | refresh lifetime, pushed back at each refresh |
| `user_sessions:<user id>` | set of the user's session ids (for "log out everywhere") | as above |
| `code:<purpose>:<email>` | hash: `code`, `attempts` | 10 min |
| `code_sent:<purpose>:<email>` | the one-minute cooldown | 60 s |
| `login_fail:<email>` | wrong passwords in a row | 15 min |
| `oauth_state:<state>` | JSON: provider, redirect URI, PKCE verifier | 10 min |

Losing Redis signs everyone out of their refresh tokens, and any pending codes
are lost. Access tokens keep working until they expire. The compose files run
Redis with `appendonly yes`.

## Decisions

**RS256 and a JWKS, not a shared secret.** A service that checks tokens gets
only the public key, so it can't mint tokens. Each service checks tokens
locally, without calling this service per request. The key id is the key's
RFC 7638 thumbprint.

**Opaque, rotating refresh tokens.** A refresh token is `<session id>.<secret>`,
and only the secret's hash is stored. Each refresh replaces the secret. Seeing
an old secret again means the token was copied, so the session ends: both the
thief and the user must sign in again. Refreshes run in a Redis transaction
(`WATCH`), so two at the same moment can't both succeed. Revocation is
immediate (logout, logout everywhere, password reset, deleted account), and
changing the signing key doesn't sign anyone out for longer than an access
token's life.

**Short access tokens.** They can't be revoked, so they last 15 minutes. Use
`/auth/me` where that matters (see integration.md).

**Commit before answering.** FastAPI runs the cleanup of a `yield` dependency
after the response is sent, so a commit there could fail after the client was
told it worked. Here each use case calls `UnitOfWork.commit()` itself. The
session dependency has `scope="function"`, so it closes (rolling back anything
not committed) before the response goes out.

**Emails after the commit.** Registration saves the account first, then sends
the code. If sending fails, the account exists and the player asks for another
code. A registration never fails because of the mail server.

**Guessing is limited.** A code allows 5 guesses (out of 1,000,000), one code a
minute per address and purpose, and codes are separate per purpose: a
confirmation code can't reset a password. A login is refused for the rest of
a 15-minute window after 10 wrong passwords for that account. An unknown email
runs a dummy bcrypt check, so it answers as slowly as a wrong password.
Forgot-password and resend answer 202 whether or not the account exists.

**bcrypt off the event loop.** A hash costs about 0.2 s of CPU, so it runs in a
worker thread (`asyncio.to_thread`). Passwords are limited to 72 bytes when
set, which is all bcrypt reads.

**Linking by email only when it's proven.** A Google account is linked to an
existing account only if Google says the email is verified. If the existing
account was never confirmed, its password is deleted: someone could have
registered the address to wait for its owner. A password reset also confirms
the email, so the owner can take an address back either way.

**OAuth with PKCE, and the tokens go to the front end.** The browser comes back
to the portal's `/auth/callback`, a page in the front end, not to this
service. The portal posts the code and the state here and gets the tokens in
the response, so they never appear in a URL. Only redirect URIs from
`OAUTH_REDIRECT_URIS` are accepted. The state, the redirect URI and the PKCE
verifier are kept server side and used once.

**Display names aren't unique.** Players are identified by `sub`. A name is
something to show, so two Jimbos are fine.

## Adding a provider

1. Add it to `OAuthProvider` (domain).
2. In `infrastructure/oauth/client.py`, list it in `providers()` when it's
   configured, and handle it in `authorization_url` and `exchange`. Return its
   stable user id, its email, and whether the provider verified that email.
3. Add its settings, and add tests with a fake of its endpoints (as
   `FakeGoogle` in `tests/conftest.py`).
