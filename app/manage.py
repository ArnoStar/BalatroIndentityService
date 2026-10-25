"""The roles from the command line, for the first admin (nobody can give
the admin role through the API before there is one):

    python -m app.manage roles                       # who has which role
    python -m app.manage show player@example.com     # one account's roles
    python -m app.manage grant player@example.com admin
    python -m app.manage revoke player@example.com tester

In Docker: ``docker compose exec identity python -m app.manage ...``. The
database is the settings' (DATABASE_URL), as for the service.
"""

import argparse
import asyncio
import sys

from app.application.dtos.roles import SetRolesInput
from app.application.exceptions.base import IdentityError
from app.application.use_cases.manage_roles import SetAccountRoles
from app.domain.exceptions import DomainError
from app.domain.value_object.email import Email
from app.domain.value_object.role import Role
from app.infrastructure.config.settings import get_settings
from app.infrastructure.sqlalchemy.repo.user_repo import SqlalchemyUserRepo
from app.infrastructure.sqlalchemy.sqlalchemy import make_engine, make_sessionmaker
from app.infrastructure.sqlalchemy.unit_of_work import SqlalchemyUnitOfWork


async def run(args: argparse.Namespace, database_url: str | None = None) -> int:
    engine = make_engine(database_url or get_settings().database_url)
    try:
        async with make_sessionmaker(engine)() as session:
            users = SqlalchemyUserRepo(session)
            if args.command == "roles":
                for role in Role:
                    accounts, _ = await users.search(None, role, 1000, 0)
                    names = ", ".join(
                        f"{u.email.value} ({u.display_name.value})" for u in accounts
                    )
                    print(f"{role.value}: {names or '-'}")
                return 0
            user = await users.get_by_email(Email(args.email))
            if user is None:
                print(f"no account with the email {args.email}", file=sys.stderr)
                return 1
            if args.command == "show":
                print(
                    f"{user.email.value} ({user.display_name.value}): "
                    f"{', '.join(sorted(r.value for r in user.roles)) or 'no role'}"
                )
                return 0
            role = Role(args.role)
            roles = (
                user.roles | {role} if args.command == "grant" else user.roles - {role}
            )
            account = await SetAccountRoles(
                users, SqlalchemyUnitOfWork(session)
            ).execute(SetRolesInput(None, user.id, frozenset(roles)))
            print(
                f"{account.email.value}: "
                f"{', '.join(r.value for r in account.roles) or 'no role'}"
            )
            return 0
    except (IdentityError, DomainError) as exc:
        print(exc, file=sys.stderr)
        return 1
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.manage",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("roles", help="who has which role")
    sub.add_parser("show", help="one account's roles").add_argument("email")
    for name in ("grant", "revoke"):
        p = sub.add_parser(name, help=f"{name} a role")
        p.add_argument("email")
        p.add_argument("role", choices=[r.value for r in Role])
    return asyncio.run(run(parser.parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
