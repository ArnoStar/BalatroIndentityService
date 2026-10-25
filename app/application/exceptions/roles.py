from app.application.exceptions.base import IdentityError


class NotAllowed(IdentityError):
    code = "forbidden"
    message = "this needs the admin role"


class LastAdmin(IdentityError):
    code = "last_admin"
    message = "the last admin keeps the admin role (give it to someone else first)"
