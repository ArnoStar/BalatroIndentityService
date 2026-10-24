import re
import secrets
from dataclasses import dataclass

from app.domain.exceptions import InvalidDisplayName

MIN_LENGTH = 3
MAX_LENGTH = 24
_ALLOWED = re.compile(r"^[\w .\-]+$")


@dataclass(frozen=True)
class DisplayName:
    """The name other players see (leaderboards, lobbies). Not unique: players
    are told apart by their id. Spaces are trimmed and collapsed."""

    value: str

    def __post_init__(self) -> None:
        normalized = " ".join(self.value.split())
        if not MIN_LENGTH <= len(normalized) <= MAX_LENGTH:
            raise InvalidDisplayName(
                f"a display name has {MIN_LENGTH} to {MAX_LENGTH} characters"
            )
        if not _ALLOWED.match(normalized):
            raise InvalidDisplayName(
                "a display name has letters, digits, spaces and . _ - only"
            )
        object.__setattr__(self, "value", normalized)

    @classmethod
    def random(cls) -> "DisplayName":
        """For an account made by a provider's sign-in (changeable later)."""
        return cls(f"Player{secrets.randbelow(10_000):04d}")
