from typing import Any
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from tests.conftest import (
    PASSWORD,
    REDIRECT_URI,
    FakeGoogle,
    Outbox,
    bearer,
    login,
    register,
)


def google_user(
    sub: str = "g-1", email: str = "player@example.com", verified: bool = True
) -> dict[str, Any]:
    return {"sub": sub, "email": email, "email_verified": verified}


def sign_in(client: TestClient, google: FakeGoogle, code: str) -> Any:
    start = client.post("/oauth/google/authorize", json={"redirect_uri": REDIRECT_URI})
    assert start.status_code == 200, start.text
    state = start.json()["state"]
    return client.post("/oauth/google/callback", json={"code": code, "state": state})


def test_providers(client: TestClient) -> None:
    assert client.get("/oauth/providers").json() == {"providers": ["google"]}


def test_authorization_url(client: TestClient) -> None:
    body = client.post(
        "/oauth/google/authorize", json={"redirect_uri": REDIRECT_URI}
    ).json()
    url = urlparse(body["authorization_url"])
    query = parse_qs(url.query)
    assert url.netloc == "accounts.google.com"
    assert query["client_id"] == ["client-id"]
    assert query["redirect_uri"] == [REDIRECT_URI]
    assert query["state"] == [body["state"]]
    assert query["code_challenge_method"] == ["S256"]


def test_only_listed_redirect_uris(client: TestClient) -> None:
    response = client.post(
        "/oauth/google/authorize", json={"redirect_uri": "https://evil.example/cb"}
    )
    assert response.status_code == 400
    assert response.json()["code"] == "redirect_uri_not_allowed"


def test_new_user(client: TestClient, google: FakeGoogle) -> None:
    google.users["c1"] = google_user()
    tokens = sign_in(client, google, "c1").json()

    me = client.get("/auth/me", headers=bearer(tokens)).json()
    assert me["email"] == "player@example.com"
    assert me["email_verified"] and not me["has_password"]
    assert me["providers"] == ["google"]
    assert me["display_name"].startswith("Player")
    # PKCE: the verifier and the redirect go with the code
    request = google.token_requests[-1]
    assert request["redirect_uri"] == REDIRECT_URI
    assert len(request["code_verifier"]) >= 43

    again = sign_in(client, google, "c1").json()
    assert client.get("/auth/me", headers=bearer(again)).json()["id"] == me["id"]


def test_a_state_works_once(client: TestClient, google: FakeGoogle) -> None:
    google.users["c1"] = google_user()
    state = client.post(
        "/oauth/google/authorize", json={"redirect_uri": REDIRECT_URI}
    ).json()["state"]
    body = {"code": "c1", "state": state}
    assert client.post("/oauth/google/callback", json=body).status_code == 200
    response = client.post("/oauth/google/callback", json=body)
    assert response.json()["code"] == "invalid_oauth_state"


def test_a_refused_code(client: TestClient, google: FakeGoogle) -> None:
    response = sign_in(client, google, "unknown")
    assert response.status_code == 400
    assert response.json()["code"] == "oauth_exchange_failed"


def test_unverified_provider_email(client: TestClient, google: FakeGoogle) -> None:
    google.users["c1"] = google_user(verified=False)
    response = sign_in(client, google, "c1")
    assert response.status_code == 403
    assert response.json()["code"] == "oauth_email_not_verified"


def test_links_to_the_account_with_that_email(
    client: TestClient, outbox: Outbox, google: FakeGoogle
) -> None:
    register(client, outbox)
    google.users["c1"] = google_user()
    tokens = sign_in(client, google, "c1").json()

    me = client.get("/auth/me", headers=bearer(tokens)).json()
    assert me["has_password"] and me["providers"] == ["google"]
    login(client)


def test_takes_an_unverified_address_back(
    client: TestClient, outbox: Outbox, google: FakeGoogle
) -> None:
    register(client, outbox, password="squatter pw", confirm=False)
    google.users["c1"] = google_user()
    tokens = sign_in(client, google, "c1").json()

    assert not client.get("/auth/me", headers=bearer(tokens)).json()["has_password"]
    response = client.post(
        "/auth/login", json={"email": "player@example.com", "password": "squatter pw"}
    )
    assert response.status_code == 401


def test_a_second_google_account_for_one_user(
    client: TestClient, outbox: Outbox, google: FakeGoogle
) -> None:
    google.users["c1"] = google_user(sub="g-1")
    sign_in(client, google, "c1")
    google.users["c2"] = google_user(sub="g-2")
    response = sign_in(client, google, "c2")
    assert response.status_code == 409


def test_unlink(client: TestClient, outbox: Outbox, google: FakeGoogle) -> None:
    google.users["c1"] = google_user()
    tokens = sign_in(client, google, "c1").json()

    response = client.delete("/oauth/google", headers=bearer(tokens))
    assert response.status_code == 409
    assert response.json()["code"] == "last_sign_in_method"

    client.post("/auth/password/forgot", json={"email": "player@example.com"})
    code = outbox.last_code("player@example.com")
    client.post(
        "/auth/password/reset",
        json={"email": "player@example.com", "code": code, "password": PASSWORD},
    )
    tokens = login(client)
    assert client.delete("/oauth/google", headers=bearer(tokens)).status_code == 204
    assert client.delete("/oauth/google", headers=bearer(tokens)).status_code == 404
