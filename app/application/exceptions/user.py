from app.application.exceptions.deps import BelFlixException


class UserAlreadyExist(BelFlixException):
    pass


class UserDoesntExist(BelFlixException):
    pass
