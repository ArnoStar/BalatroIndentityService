from dataclasses import dataclass


@dataclass(frozen=True)
class AccessToken:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Access token cannot be empty")


@dataclass(frozen=True)
class RefreshToken:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Refresh token cannot be empty")
