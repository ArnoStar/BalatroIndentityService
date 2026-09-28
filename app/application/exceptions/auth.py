from app.application.exceptions.deps import BelFlixException


class InvalidEmailOrPassword(BelFlixException):
    pass


class InvalidOAuthState(BelFlixException):
    pass
