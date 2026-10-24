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
    def from_profile(cls, name: str | None) -> "DisplayName":
        """The closest valid name to a provider's profile name (characters
        that aren't allowed dropped, cut to the maximum length), or a random
        one when too little is left."""
        if name:
            kept = "".join(c if _ALLOWED.match(c) else " " for c in name)
            kept = " ".join(kept.split())[:MAX_LENGTH].strip()
            if len(kept) >= MIN_LENGTH:
                return cls(kept)
        return cls.random()

    @classmethod
    def random(cls) -> "DisplayName":
        """For an account made by a provider's sign-in (changeable later)."""
        return cls(f"Player{secrets.randbelow(10_000):04d}")
