# Using the tokens

## In a service: checking an access token

An access token is a JWT signed with RS256:

```json
// header
{"alg": "RS256", "kid": "Bg1uW_7_X09gbHIpDR11p0HHbOQ_dqL5QvXqjaygxL8", "typ": "JWT"}
// payload
{
  "iss": "https://example.com/identity",   // PUBLIC_URL
  "aud": "balatro",                        // JWT_AUDIENCE
  "sub": "5a68c181-8295-48a4-be76-90596b92e45b",  // the account id: the player
  "name": "Jimbo",                         // the display name when it was issued
  "iat": 1792873378, "exp": 1792874278,
  "jti": "9f0c…",
  "typ": "access"
}
```

A service accepts a token when all of these hold:

1. The signature is valid with the key named by `kid`, from
   `GET <identity>/.well-known/jwks.json`. Cache the key set. Fetch it again
   when a token names a `kid` you don't have (the key changed), but not on
   every request.
2. `alg` is `RS256`. Never accept the algorithm the token asks for.
3. `iss` is exactly the identity service's `PUBLIC_URL`, and `aud` is
   `balatro`.
4. `exp` is in the future (allow some clock leeway, such as 30 s).
5. `typ` is `access`.

Then `sub` is the player. Store your data by `sub`, never by email or
display name: those change.

In Python with PyJWT (this is what BalatroWebAPI does, in
`infrastructure/auth.py`):

```python
import jwt

keys = jwt.PyJWKClient(
    "http://identity:8000/.well-known/jwks.json", cache_keys=True, lifespan=300
)


def player_id(token: str) -> str:
    key = keys.get_signing_key_from_jwt(token)  # by kid, cached
    claims = jwt.decode(
        token,
        key.key,
        algorithms=["RS256"],
        audience="balatro",
        issuer="https://example.com/identity",
        leeway=30,
        options={"require": ["exp", "iat", "sub", "iss", "aud"]},
    )
    if claims.get("typ") != "access":
        raise jwt.InvalidTokenError("not an access token")
    return claims["sub"]
```

Answer a missing or refused token with `401` and
`WWW-Authenticate: Bearer error="invalid_token"`. The client then refreshes and
tries again.

Inside Docker, fetch the keys over the internal network
(`http://identity:8000/...`). The issuer to expect is still the public URL,
since that is what the service writes in `iss`.

**What a valid token doesn't tell you:** an access token stays valid until it
expires, up to 15 minutes, even after a logout, a password reset or a deleted
account. For something that must not survive those (payments, deleting data),
call `GET /auth/me` with the token as well.

## In a browser: the session

The portal (BalatroPortal) and the game (BalatroFrontEnd) share one session,
because they are served from one origin. It is stored in `localStorage`:

```js
localStorage['balatro.session'] = JSON.stringify({
  access_token, refresh_token,
  expires_at,   // Date.now() + expires_in * 1000
});
```

Both apps keep to these rules (`src/shared/api/session.ts` in each):

- Before a request, if the access token expires in less than 30 s, refresh
  first.
- On a `401` from a service, refresh once and send the request again. If the
  refresh fails, the player is signed out.
- **Refresh under a cross-tab lock**
  (`navigator.locks.request('balatro.session', ...)`). Inside the lock, read
  the entry again: another tab may have refreshed it already. Two tabs using
  the same refresh token would look like a stolen token, and the service would
  end the session.
- A refresh that answers 401 means the session is over: remove the entry.
- Signing out: remove the entry, then `POST /auth/logout` with the refresh
  token.

Only the portal signs in: the game sends the player to
`/login?next=<the game's URL>`, and the portal sends them back afterwards. The
portal only follows `next` values that are paths on the same site.

Google sign-in, from the portal:

1. `POST /oauth/google/authorize` with
   `{"redirect_uri": "<origin>/auth/callback"}`. Remember `next` in
   `sessionStorage`, then go to `authorization_url`.
2. Google sends the browser back to `/auth/callback?code=…&state=…`. The page
   posts both to `/oauth/google/callback`, stores the tokens, and goes to
   `next`.

Use each code once. React's development mode runs effects twice, so guard the
callback, as the portal does.

Linking from the account page works the same way, with
`POST /oauth/google/link` (with the access token) in place of `authorize`. The
callback's tokens are a new session for the same account: store them, and log
out the old refresh token.
