from fastapi import APIRouter, Depends

from app.application.dtos.user import RegisterUserInput
from app.bootstrap.container import RequestContainer
from app.domain.value_object.email import Email
from app.presentation.api.dependencies import get_container
from app.presentation.api.schemas.auth import RegisterUserRequest

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
async def register_user(
    request: RegisterUserRequest,
    container: RequestContainer = Depends(get_container),
):
    dto: RegisterUserInput = RegisterUserInput(
        email=Email(request.email), password=request.password
    )

    user = await container.register_user.execute(dto)

    return user
