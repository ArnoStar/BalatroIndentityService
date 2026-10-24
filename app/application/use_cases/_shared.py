"""Steps several use cases share."""

import logging

from app.application.dtos.tokens import TokenPair
from app.application.exceptions.auth import TooManyAttempts
from app.application.exceptions.email import EmailDeliveryFailed
from app.application.ports.code_sender import CodeSender
from app.application.ports.confirmation_codes import CodePurpose, ConfirmationCodes
from app.application.ports.session_store import SessionStore
from app.application.ports.token_issuer import AccessTokenIssuer
from app.domain.entities.user import User
from app.domain.value_object.email import Email

log = logging.getLogger(__name__)


async def issue_tokens(
    access_tokens: AccessTokenIssuer,
    sessions: SessionStore,
    user: User,
) -> TokenPair:
    access = access_tokens.issue(user)
    refresh = await sessions.create(user.id)
    return TokenPair(access.value, refresh, access.expires_in)


async def send_code(
    codes: ConfirmationCodes,
    code_sender: CodeSender,
    purpose: CodePurpose,
    email: Email,
) -> None:
    code = await codes.issue(purpose, email)
    await code_sender.send_code(email, purpose, code)


async def try_send_code(
    codes: ConfirmationCodes,
    code_sender: CodeSender,
    purpose: CodePurpose,
    email: Email,
) -> None:
    """``send_code`` after a change that is already saved: an email that
    fails (or waits for the cooldown) is logged, and the user asks for another
    code."""
    try:
        await send_code(codes, code_sender, purpose, email)
    except (EmailDeliveryFailed, TooManyAttempts):
        log.warning("could not send the %s code", purpose, exc_info=True)
