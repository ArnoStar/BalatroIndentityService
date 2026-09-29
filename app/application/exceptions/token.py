from app.application.exceptions.deps import BelFlixException


class InvalidToken(BelFlixException):
    pass


class WrongTokenType(BelFlixException):
    pass
