from app.application.exceptions.base import IdentityError


class UserAlreadyExist(IdentityError):
    code = "user_exists"
    message = "an account with this email already exists"


class UserDoesntExist(IdentityError):
    code = "user_not_found"
    message = "no such user"
