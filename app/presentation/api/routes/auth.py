from fastapi import APIRouter, Depends

from app.application.dtos.user import RegisterUserDTO
from app.bootstrap.container import RequestContainer
from app.domain.value_object.email import Email
from app.presentation.api.dependencies import get_container
from app.presentation.api.schemas.auth import RegisterUserRequest

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/users")
async def register_user(
    request: RegisterUserRequest,
    container: RequestContainer = Depends(get_container),
):
    dto: RegisterUserDTO = RegisterUserDTO(
        email=Email(request.email),
    )

    user = await container.register_user.execute(dto)

    return user
