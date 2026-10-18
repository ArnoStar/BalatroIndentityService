from app.application.exceptions.deps import BelFlixException


class OAuthAccountDoesntExist(BelFlixException):
    pass


class RedirectUriNotSet(BelFlixException):
    pass
