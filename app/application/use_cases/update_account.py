from app.application.dtos.authentication import UpdateAccountInput
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.unit_of_work import UnitOfWork


class UpdateAccount:
    """Changes what the user may change about their account (the display
    name). The access tokens carry the old name until they are refreshed."""

    def __init__(self, user_repo: UserRepo, unit_of_work: UnitOfWork) -> None:
        self.user_repo = user_repo
        self.unit_of_work = unit_of_work

    async def execute(self, dto: UpdateAccountInput) -> None:
        if dto.display_name is not None:
            await self.user_repo.set_display_name(dto.user_id, dto.display_name)
        await self.unit_of_work.commit()
