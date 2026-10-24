from app.application.exceptions.base import IdentityError


class InvalidOAuthState(IdentityError):
    code = "invalid_oauth_state"
    message = "the sign-in attempt is unknown or has expired, start again"


class OAuthProviderNotConfigured(IdentityError):
    code = "oauth_provider_disabled"
    message = "this sign-in provider is not configured on the server"


class RedirectUriNotAllowed(IdentityError):
    code = "redirect_uri_not_allowed"
    message = "this redirect_uri is not in OAUTH_REDIRECT_URIS"


class OAuthExchangeFailed(IdentityError):
    code = "oauth_exchange_failed"
    message = "the sign-in provider refused the authorization code"


class OAuthEmailNotVerified(IdentityError):
    code = "oauth_email_not_verified"
    message = "the provider's account has no verified email address"


class OAuthAccountDoesntExist(IdentityError):
    code = "oauth_account_not_found"
    message = "this account is not linked to that provider"


class LastSignInMethod(IdentityError):
    code = "last_sign_in_method"
    message = "set a password before unlinking the only way to sign in"


class OAuthAccountConflict(IdentityError):
    code = "oauth_account_conflict"
    message = "this account is already linked to another account of that provider"
