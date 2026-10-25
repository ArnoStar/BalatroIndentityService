from enum import StrEnum


class Role(StrEnum):
    """What an account may do beyond playing. The identity service gives
    roles; each service decides what a role allows there (its permissions).
    A new role is added here, to ``ROLE_DESCRIPTIONS``, and to the services
    that grant it something (docs/integration.md)."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    TESTER = "tester"


ROLE_DESCRIPTIONS: dict[Role, str] = {
    Role.ADMIN: "manages accounts' roles; everything a developer may do",
    Role.DEVELOPER: "reads the bug reports and rebuilds runs from them",
    Role.TESTER: "uses the game's test helpers (money, jokers, bosses) in their runs",
}
