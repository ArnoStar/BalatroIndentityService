from app.application.dtos.authentication import LogoutAllInput, LogoutInput
from app.application.ports.session_store import SessionStore


class Logout:
    """Ends the session of a refresh token. Its access token stays valid
    until it expires (a few minutes)."""

    def __init__(self, sessions: SessionStore) -> None:
        self.sessions = sessions

    async def execute(self, dto: LogoutInput) -> None:
        await self.sessions.revoke(dto.refresh_token)


class LogoutAll:
    """Ends every session of the user."""

    def __init__(self, sessions: SessionStore) -> None:
        self.sessions = sessions

    async def execute(self, dto: LogoutAllInput) -> None:
        await self.sessions.revoke_all(dto.user_id)
