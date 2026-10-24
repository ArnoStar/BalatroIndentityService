class IdentityError(Exception):
    """An error of a use case. ``code`` is stable (clients switch on it);
    the presentation layer maps each class to an HTTP status."""

    code = "identity_error"
    message = "identity error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message
