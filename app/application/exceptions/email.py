from app.application.exceptions.base import IdentityError


class EmailDeliveryFailed(IdentityError):
    code = "email_delivery_failed"
    message = "the email could not be sent, try again later"
