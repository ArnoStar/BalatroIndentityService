"""Roles: the first admin from the command line, then admins give roles, and
the access tokens name them."""

import asyncio
from argparse import Namespace
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient

from app import manage
from app.infrastructure.config.settings import Settings
from tests.conftest import Outbox, bearer, login, register

ADMIN = "admin@example.com"
PLAYER = "player@example.com"


def cli(settings: Settings, command: str, email: str = "", role: str = "") -> int:
    args = Namespace(command=command, email=email, role=role)
    return asyncio.run(manage.run(args, settings.database_url))


def claims(tokens: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = jwt.decode(
        tokens["access_token"], options={"verify_signature": False}
    )
    return payload


@pytest.fixture
def admin(client: TestClient, outbox: Outbox, settings: Settings) -> dict[str, Any]:
    register(client, outbox, ADMIN, name="Admin")
    register(client, outbox, PLAYER, name="Player")
    assert cli(settings, "grant", ADMIN, "admin") == 0
    return login(client, ADMIN)


def test_roles_are_listed(client: TestClient) -> None:
    roles = {r["role"] for r in client.get("/roles").json()}
    assert roles == {"admin", "developer", "tester"}


def test_the_token_names_the_roles(client: TestClient, admin: dict[str, Any]) -> None:
    assert claims(admin)["roles"] == ["admin"]
    assert client.get("/auth/me", headers=bearer(admin)).json()["roles"] == ["admin"]
    assert claims(login(client, PLAYER))["roles"] == []


def test_admins_give_roles(
    client: TestClient, admin: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    player = login(client, PLAYER)
    page = client.get(
        "/admin/accounts", params={"query": "PLAY"}, headers=bearer(admin)
    )
    assert page.status_code == 200, page.text
    assert page.json()["total"] == 1
    target = page.json()["accounts"][0]
    assert (target["email"], target["roles"]) == (PLAYER, [])

    r = client.put(
        f"/admin/accounts/{target['id']}/roles",
        json={"roles": ["tester", "developer"]},
        headers=bearer(admin),
    )
    assert r.status_code == 200, r.text
    assert r.json()["roles"] == ["developer", "tester"]
    assert client.get("/auth/me", headers=bearer(player)).json()["roles"] == [
        "developer",
        "tester",
    ]
    # the old access token says nothing new; the next one does
    assert claims(player)["roles"] == []
    refreshed = client.post(
        "/auth/refresh", json={"refresh_token": player["refresh_token"]}
    ).json()
    assert claims(refreshed)["roles"] == ["developer", "tester"]

    developers = client.get(
        "/admin/accounts", params={"role": "developer"}, headers=bearer(admin)
    ).json()
    assert [a["email"] for a in developers["accounts"]] == [PLAYER]
    assert cli(client.app.state.container.settings, "roles") == 0  # type: ignore[attr-defined]
    assert f"developer: {PLAYER} (Player)" in capsys.readouterr().out


def test_only_admins_see_and_change_roles(
    client: TestClient, admin: dict[str, Any]
) -> None:
    player = login(client, PLAYER)
    me = client.get("/auth/me", headers=bearer(player)).json()
    r = client.get("/admin/accounts", headers=bearer(player))
    assert r.status_code == 403 and r.json()["code"] == "forbidden"
    r = client.put(
        f"/admin/accounts/{me['id']}/roles",
        json={"roles": ["admin"]},
        headers=bearer(player),
    )
    assert r.status_code == 403
    assert client.get("/admin/accounts").status_code == 401


def test_the_last_admin_stays(
    client: TestClient, admin: dict[str, Any], settings: Settings
) -> None:
    me = client.get("/auth/me", headers=bearer(admin)).json()
    r = client.put(
        f"/admin/accounts/{me['id']}/roles", json={"roles": []}, headers=bearer(admin)
    )
    assert r.status_code == 409 and r.json()["code"] == "last_admin"
    assert cli(settings, "revoke", ADMIN, "admin") == 1
    assert cli(settings, "grant", PLAYER, "admin") == 0
    r = client.put(
        f"/admin/accounts/{me['id']}/roles", json={"roles": []}, headers=bearer(admin)
    )
    assert r.status_code == 200 and r.json()["roles"] == []
    # no longer an admin, at once (the API checks the database, not the token)
    assert client.get("/admin/accounts", headers=bearer(admin)).status_code == 403


def test_bad_requests(client: TestClient, admin: dict[str, Any]) -> None:
    me = client.get("/auth/me", headers=bearer(admin)).json()
    r = client.put(
        f"/admin/accounts/{me['id']}/roles",
        json={"roles": ["emperor"]},
        headers=bearer(admin),
    )
    assert r.status_code == 422
    r = client.put(
        "/admin/accounts/00000000-0000-0000-0000-000000000000/roles",
        json={"roles": []},
        headers=bearer(admin),
    )
    assert r.status_code == 404 and r.json()["code"] == "user_not_found"


def test_the_command_line_needs_an_account(
    settings: Settings, client: TestClient
) -> None:
    assert cli(settings, "grant", "nobody@example.com", "admin") == 1


def test_deleting_an_account_deletes_its_roles(
    client: TestClient, outbox: Outbox, admin: dict[str, Any], settings: Settings
) -> None:
    assert cli(settings, "grant", PLAYER, "tester") == 0
    assert (
        client.delete("/auth/me", headers=bearer(login(client, PLAYER))).status_code
        == 204
    )
    page = client.get(
        "/admin/accounts", params={"role": "tester"}, headers=bearer(admin)
    )
    assert page.json()["total"] == 0


def test_the_command_line_shows_an_account(
    settings: Settings, admin: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli(settings, "show", ADMIN) == 0
    assert capsys.readouterr().out.strip() == f"{ADMIN} (Admin): admin"
    assert cli(settings, "show", PLAYER) == 0
    assert capsys.readouterr().out.strip() == f"{PLAYER} (Player): no role"
    assert cli(settings, "show", "nobody@example.com") == 1
