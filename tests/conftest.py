"""The service with in-process stand-ins: SQLite for PostgreSQL, fakeredis for
Redis, an outbox for the emails and a mocked Google."""

import asyncio
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import pytest
from fakeredis import FakeAsyncRedis
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.bootstrap.container import Container
from app.domain.value_object.email import Email
from app.infrastructure.bcrypt import BcryptPasswordHasher
from app.infrastructure.config.settings import Settings
from app.infrastructure.jwt.keys import SigningKey, generate_pem
from app.infrastructure.sqlalchemy import model  # noqa: F401 (registers the tables)
from app.infrastructure.sqlalchemy.sqlalchemy import Base
from app.main import create_app

PASSWORD = "correct horse"
REDIRECT_URI = "http://localhost:5174/auth/callback"


@dataclass
class Outbox:
    sent: list[tuple[str, str, str]] = field(default_factory=list)

    async def send(self, email: Email, subject: str, body: str) -> None:
        self.sent.append((email.value, subject, body))

    def last_code(self, to: str) -> str:
        for address, _, body in reversed(self.sent):
            if address == to:
                match = re.search(r"\b(\d{6})\b", body)
                assert match, body
                return match.group(1)
        raise AssertionError(f"no email to {to}")


@dataclass
class FakeGoogle:
    """Google's token and userinfo endpoints: a code is the userinfo it gives."""

    users: dict[str, dict[str, Any]] = field(default_factory=dict)
    token_requests: list[dict[str, str]] = field(default_factory=list)

    def handler(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            form = dict(httpx.QueryParams(request.content.decode()))
            self.token_requests.append(form)
            if form["code"] not in self.users:
                return httpx.Response(400, json={"error": "invalid_grant"})
            return httpx.Response(200, json={"access_token": f"at-{form['code']}"})
        if request.url.path == "/v1/userinfo":
            code = request.headers["Authorization"].removeprefix("Bearer at-")
            return httpx.Response(200, json=self.users[code])
        return httpx.Response(404)


@pytest.fixture(scope="session")
def signing_key() -> SigningKey:
    return SigningKey.from_pem(generate_pem())


@pytest.fixture(scope="session")
def hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher(rounds=4)  # fast


@pytest.fixture
def outbox() -> Outbox:
    return Outbox()


@pytest.fixture
def google() -> FakeGoogle:
    return FakeGoogle()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'identity.db'}",
        public_url="http://identity.test",
        google_client_id="client-id",
        google_client_secret="client-secret",
        oauth_redirect_uris=[REDIRECT_URI],
        cors_origins=["http://localhost:5173"],
    )


async def _create_tables(url: str) -> None:
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture
def client(
    settings: Settings,
    signing_key: SigningKey,
    hasher: BcryptPasswordHasher,
    outbox: Outbox,
    google: FakeGoogle,
) -> Iterator[TestClient]:
    asyncio.run(_create_tables(settings.database_url))

    def container(s: Settings) -> Container:
        return Container(
            s,
            redis=FakeAsyncRedis(decode_responses=True),
            http=httpx.AsyncClient(transport=httpx.MockTransport(google.handler)),
            email_sender=outbox,
            signing_key=signing_key,
            password_hasher=hasher,
        )

    with TestClient(create_app(settings, container)) as test_client:
        yield test_client


def register(
    client: TestClient,
    outbox: Outbox,
    email: str = "player@example.com",
    password: str = PASSWORD,
    name: str = "Player",
    confirm: bool = True,
) -> None:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": name},
    )
    assert response.status_code == 201, response.text
    if confirm:
        code = outbox.last_code(email.lower())
        response = client.post(
            "/auth/confirm-email", json={"email": email, "code": code}
        )
        assert response.status_code == 204, response.text


def login(
    client: TestClient, email: str = "player@example.com", password: str = PASSWORD
) -> dict[str, Any]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    tokens: dict[str, Any] = response.json()
    return tokens


def bearer(tokens: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
