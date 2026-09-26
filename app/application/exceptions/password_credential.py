from app.application.exceptions.deps import BelFlixException


class PasswordCredentialAlreadyExist(BelFlixException):
    pass


class PasswordCredentialDoesntExist(BelFlixException):
    pass
