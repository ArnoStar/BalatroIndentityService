from dataclasses import dataclass

from app.domain.entities.token_pair import TokenPair
from app.domain.value_object.email import Email


@dataclass(frozen=True)
class AuthUserInput:
    email: Email
    password: str


@dataclass(frozen=True)
class AuthUserOutput:
    token_pair: TokenPair
