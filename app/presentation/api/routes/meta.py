from typing import Any

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.presentation.api.dependencies import AppContainer

router = APIRouter(tags=["Meta"])


@router.get("/health", summary="Is the service up (and its database and Redis)")
async def health(container: AppContainer, response: Response) -> dict[str, str]:
    checks: dict[str, str] = {}
    try:
        async with container.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:  # noqa: BLE001 (any failure means it is down)
        checks["database"] = "down"
    try:
        await container.redis.ping()
        checks["redis"] = "ok"
    except Exception:  # noqa: BLE001
        checks["redis"] = "down"

    ok = all(value == "ok" for value in checks.values())
    if not ok:
        response.status_code = 503
    return {"status": "ok" if ok else "degraded", **checks}


@router.get(
    "/.well-known/jwks.json",
    summary="The public keys that verify the access tokens",
)
def jwks(container: AppContainer, response: Response) -> dict[str, Any]:
    """Services that accept the access tokens verify their RS256 signature
    with these keys (by ``kid``), and check ``iss`` and ``aud``."""
    response.headers["Cache-Control"] = "public, max-age=300"
    return container.signing_key.jwks()
