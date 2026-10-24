import jwt
from fastapi.testclient import TestClient

from tests.conftest import PASSWORD, Outbox, bearer, login, register


def test_health_and_jwks(client: TestClient) -> None:
    assert client.get("/health").json() == {
        "status": "ok",
        "database": "ok",
        "redis": "ok",
    }
    keys = client.get("/.well-known/jwks.json").json()["keys"]
    assert keys[0]["kty"] == "RSA" and keys[0]["alg"] == "RS256"


def test_register_confirm_login(client: TestClient, outbox: Outbox) -> None:
    register(client, outbox, email="Player@Example.COM", name="  Lucky   Cat ")
    tokens = login(client, email="player@example.com")
    assert tokens["token_type"] == "Bearer"
    assert tokens["expires_in"] == 15 * 60

    me = client.get("/auth/me", headers=bearer(tokens)).json()
    assert me["email"] == "player@example.com"
    assert me["display_name"] == "Lucky Cat"
    assert me["email_verified"] and me["has_password"]
    assert me["providers"] == []


def test_access_token_verifies_with_jwks(client: TestClient, outbox: Outbox) -> None:
    register(client, outbox)
    token = login(client)["access_token"]
    jwk = client.get("/.well-known/jwks.json").json()["keys"][0]

    header = jwt.get_unverified_header(token)
    assert header["kid"] == jwk["kid"]
    claims = jwt.decode(
        token,
        jwt.PyJWK(jwk).key,
        algorithms=["RS256"],
        audience="balatro",
        issuer="http://identity.test",
    )
    me = client.get("/auth/me", headers=bearer({"access_token": token})).json()
    assert claims["sub"] == me["id"]
    assert claims["name"] == "Player"
    assert claims["typ"] == "access"


def test_login_needs_a_verified_email(client: TestClient, outbox: Outbox) -> None:
    register(client, outbox, confirm=False)
    response = client.post(
        "/auth/login", json={"email": "player@example.com", "password": PASSWORD}
    )
    assert response.status_code == 403
    assert response.json()["code"] == "email_not_verified"


def test_wrong_password_and_unknown_email_look_the_same(
    client: TestClient, outbox: Outbox
) -> None:
    register(client, outbox)
    wrong = client.post(
        "/auth/login", json={"email": "player@example.com", "password": "nope nope"}
    )
    unknown = client.post(
        "/auth/login", json={"email": "who@example.com", "password": PASSWORD}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_register_twice(client: TestClient, outbox: Outbox) -> None:
    register(client, outbox, email="a@example.com", confirm=False)
    again = client.post(
        "/auth/register",
        json={"email": "A@example.com", "password": PASSWORD, "display_name": "Abc"},
    )
    assert again.json()["code"] == "email_not_verified"

    register(client, outbox, email="b@example.com")
    again = client.post(
        "/auth/register",
        json={"email": "b@example.com", "password": PASSWORD, "display_name": "Abc"},
    )
    assert again.status_code == 409
    assert again.json()["code"] == "user_exists"


def test_password_and_name_rules(client: TestClient) -> None:
    for password, name, code in [
        ("short", "Player", "invalid_password"),
        ("é" * 37, "Player", "invalid_password"),  # 74 bytes: more than bcrypt reads
        (PASSWORD, "ab", "invalid_display_name"),
        (PASSWORD, "<script>", "invalid_display_name"),
    ]:
        response = client.post(
            "/auth/register",
            json={"email": "p@example.com", "password": password, "display_name": name},
        )
        assert response.status_code == 422, (password, name)
        assert response.json()["code"] == code
    response = client.post(
        "/auth/register", json={"email": "not an email", "password": PASSWORD}
    )
    assert response.json()["code"] == "invalid_request"


def test_resend_confirmation(client: TestClient, outbox: Outbox) -> None:
    response = client.post(
        "/auth/resend-confirmation", json={"email": "nobody@example.com"}
    )
    assert response.status_code == 202
    assert outbox.sent == []

    register(client, outbox, confirm=False)
    # the registration's code was sent moments ago
    response = client.post(
        "/auth/resend-confirmation", json={"email": "player@example.com"}
    )
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0


def test_a_code_allows_five_guesses(client: TestClient, outbox: Outbox) -> None:
    register(client, outbox, confirm=False)
    code = outbox.last_code("player@example.com")
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        response = client.post(
            "/auth/confirm-email", json={"email": "player@example.com", "code": wrong}
        )
        assert response.json()["code"] == "invalid_code"
    response = client.post(
        "/auth/confirm-email", json={"email": "player@example.com", "code": code}
    )
    assert response.status_code == 400


def test_a_code_works_once(client: TestClient, outbox: Outbox) -> None:
    register(client, outbox)
    code = outbox.last_code("player@example.com")
    response = client.post(
        "/auth/confirm-email", json={"email": "player@example.com", "code": code}
    )
    assert response.status_code == 400


def test_refresh_rotates_and_detects_reuse(client: TestClient, outbox: Outbox) -> None:
    register(client, outbox)
    first = login(client)

    second = client.post("/auth/refresh", json=first).json()
    assert second["refresh_token"] != first["refresh_token"]
    assert client.get("/auth/me", headers=bearer(second)).status_code == 200

    # the old one again: someone copied it, so the session ends for both
    replay = client.post("/auth/refresh", json=first)
    assert replay.status_code == 401
    assert replay.headers["WWW-Authenticate"].startswith("Bearer")
    assert client.post("/auth/refresh", json=second).status_code == 401


def test_refresh_token_is_not_an_access_token(
    client: TestClient, outbox: Outbox
) -> None:
    register(client, outbox)
    tokens = login(client)
    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )
    assert response.status_code == 401
    response = client.post(
        "/auth/refresh", json={"refresh_token": tokens["access_token"][:200]}
    )
    assert response.status_code == 401


def test_logout(client: TestClient, outbox: Outbox) -> None:
    register(client, outbox)
    one, two = login(client), login(client)

    assert client.post("/auth/logout", json=one).status_code == 204
    assert client.post("/auth/refresh", json=one).status_code == 401
    assert client.post("/auth/refresh", json=two).status_code == 200


def test_logout_all(client: TestClient, outbox: Outbox) -> None:
    register(client, outbox)
    one, two = login(client), login(client)

    assert client.post("/auth/logout-all", headers=bearer(one)).status_code == 204
    assert client.post("/auth/refresh", json=one).status_code == 401
    assert client.post("/auth/refresh", json=two).status_code == 401


def test_an_access_token_is_required(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"
    response = client.get("/auth/me", headers={"Authorization": "Bearer junk"})
    assert response.status_code == 401


def test_logins_are_throttled(client: TestClient, outbox: Outbox) -> None:
    register(client, outbox)
    for _ in range(10):
        response = client.post(
            "/auth/login", json={"email": "player@example.com", "password": "x" * 8}
        )
        assert response.status_code == 401
    response = client.post(
        "/auth/login", json={"email": "player@example.com", "password": PASSWORD}
    )
    assert response.status_code == 429
    assert response.json()["code"] == "too_many_attempts"


def test_password_reset(client: TestClient, outbox: Outbox) -> None:
    response = client.post("/auth/password/forgot", json={"email": "no@example.com"})
    assert response.status_code == 202
    assert outbox.sent == []

    register(client, outbox)
    session = login(client)
    client.post("/auth/password/forgot", json={"email": "player@example.com"})
    code = outbox.last_code("player@example.com")

    response = client.post(
        "/auth/password/reset",
        json={"email": "player@example.com", "code": code, "password": "new password"},
    )
    assert response.status_code == 204
    assert client.post("/auth/refresh", json=session).status_code == 401
    assert (
        client.post(
            "/auth/login", json={"email": "player@example.com", "password": PASSWORD}
        ).status_code
        == 401
    )
    login(client, password="new password")


def test_password_reset_verifies_the_email(client: TestClient, outbox: Outbox) -> None:
    # someone registered the address first: its owner takes it back
    register(client, outbox, password="squatter pw", confirm=False)
    client.post("/auth/password/forgot", json={"email": "player@example.com"})
    code = outbox.last_code("player@example.com")
    client.post(
        "/auth/password/reset",
        json={"email": "player@example.com", "code": code, "password": PASSWORD},
    )
    login(client)


def test_a_verification_code_doesnt_reset_a_password(
    client: TestClient, outbox: Outbox
) -> None:
    register(client, outbox, confirm=False)
    code = outbox.last_code("player@example.com")
    response = client.post(
        "/auth/password/reset",
        json={"email": "player@example.com", "code": code, "password": "x" * 10},
    )
    assert response.status_code == 400


def test_update_display_name(client: TestClient, outbox: Outbox) -> None:
    register(client, outbox)
    tokens = login(client)
    response = client.patch(
        "/auth/me", headers=bearer(tokens), json={"display_name": "Jimbo"}
    )
    assert response.json()["display_name"] == "Jimbo"
    response = client.patch(
        "/auth/me", headers=bearer(tokens), json={"display_name": ""}
    )
    assert response.status_code == 422


def test_delete_account(client: TestClient, outbox: Outbox) -> None:
    register(client, outbox)
    tokens = login(client)

    assert client.delete("/auth/me", headers=bearer(tokens)).status_code == 204
    assert client.post("/auth/refresh", json=tokens).status_code == 401
    assert client.get("/auth/me", headers=bearer(tokens)).status_code == 401
    # the address is free again
    register(client, outbox, confirm=False)
