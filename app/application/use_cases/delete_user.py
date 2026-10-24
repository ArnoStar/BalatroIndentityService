from app.application.dtos.authentication import DeleteUserInput
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.session_store import SessionStore
from app.application.ports.unit_of_work import UnitOfWork


class DeleteUser:
    def __init__(
        self,
        user_repo: UserRepo,
        unit_of_work: UnitOfWork,
        sessions: SessionStore,
    ) -> None:
        self.user_repo = user_repo
        self.unit_of_work = unit_of_work
        self.sessions = sessions

    async def execute(self, dto: DeleteUserInput) -> None:
        await self.user_repo.delete_by_id(dto.user_id)
        await self.unit_of_work.commit()
        await self.sessions.revoke_all(dto.user_id)
