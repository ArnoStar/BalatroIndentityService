from dataclasses import dataclass


@dataclass(frozen=True)
class PasswordHash:
    value: str

    def __post_init__(self):
        if len(self.value) == 0:
            raise ValueError("IPassword hash can't be empty")
