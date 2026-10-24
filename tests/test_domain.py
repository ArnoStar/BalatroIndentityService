import pytest

from app.domain.exceptions import InvalidDisplayName, InvalidEmail, InvalidPassword
from app.domain.value_object.display_name import DisplayName
from app.domain.value_object.email import Email
from app.domain.value_object.password import Password
from app.infrastructure.config.settings import Settings


def test_email_is_normalized() -> None:
    assert Email("  Jimbo@Example.COM ").value == "jimbo@example.com"
    assert Email("a@b.co") == Email("A@B.CO")


@pytest.mark.parametrize("value", ["", "jimbo", "@example.com", "jimbo@localhost"])
def test_invalid_email(value: str) -> None:
    with pytest.raises(InvalidEmail):
        Email(value)


def test_password_bounds() -> None:
    Password("12345678")
    Password("a" * 72)
    with pytest.raises(InvalidPassword):
        Password("1234567")
    with pytest.raises(InvalidPassword):
        Password("a" * 73)
    assert "secret" not in repr(Password("secret password"))


def test_display_name() -> None:
    assert DisplayName("  Lucky   Cat ").value == "Lucky Cat"
    assert DisplayName("Jöker_1.2-3").value == "Jöker_1.2-3"
    assert len(DisplayName.random().value) == 10
    for bad in ["ab", "  a  ", "x" * 25, "a<b>c", "new\nline\x00"]:
        with pytest.raises(InvalidDisplayName):
            DisplayName(bad)


def test_settings_lists_from_commas(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://a.example, https://b.example")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.cors_origins == ["https://a.example", "https://b.example"]
    assert settings.google_client_id is None
    assert not settings.google_enabled
