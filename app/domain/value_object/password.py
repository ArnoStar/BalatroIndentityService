from dataclasses import dataclass

from app.domain.exceptions import InvalidPassword

MIN_LENGTH = 8
# bcrypt only reads the first 72 bytes of a password (and bcrypt>=5 refuses more)
MAX_BYTES = 72


@dataclass(frozen=True)
class Password:
    """A new password, as the user typed it. Only passwords being set are
    checked; a login compares whatever was typed."""

    value: str

    def __post_init__(self) -> None:
        if len(self.value) < MIN_LENGTH:
            raise InvalidPassword(
                f"a password has at least {MIN_LENGTH} characters",
            )
        if len(self.value.encode("utf-8")) > MAX_BYTES:
            raise InvalidPassword(f"a password has at most {MAX_BYTES} bytes")

    def __repr__(self) -> str:
        return "Password(***)"


@dataclass(frozen=True)
class PasswordHash:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("a password hash can't be empty")

    def __repr__(self) -> str:
        return "PasswordHash(***)"
