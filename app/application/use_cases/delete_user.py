from app.application.dtos.authentication import DeleteUserInput
from app.application.ports.repo.user_repo import UserRepo


class DeleteUser:
    def __init__(self, user_repo: UserRepo) -> None:
        self.user_repo = user_repo

    async def execute(self, dto: DeleteUserInput) -> None:
        await self.user_repo.delete_by_id(dto.user_id)
