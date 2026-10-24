"""The RS256 key pair that signs the access tokens. Other services verify
them with the public half, published as a JWKS (``/.well-known/jwks.json``)."""

import base64
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

log = logging.getLogger(__name__)


def _b64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


@dataclass(frozen=True)
class SigningKey:
    private_key: rsa.RSAPrivateKey
    kid: str
    public_jwk: dict[str, Any]

    @classmethod
    def from_pem(cls, pem: bytes) -> "SigningKey":
        key = serialization.load_pem_private_key(pem, password=None)
        if not isinstance(key, rsa.RSAPrivateKey):
            raise TypeError("the JWT signing key must be an RSA private key")
        numbers = key.public_key().public_numbers()
        e, n = _b64url_uint(numbers.e), _b64url_uint(numbers.n)
        # the key id is the key's RFC 7638 thumbprint
        thumbprint = json.dumps(
            {"e": e, "kty": "RSA", "n": n}, separators=(",", ":"), sort_keys=True
        )
        kid = (
            base64.urlsafe_b64encode(hashlib.sha256(thumbprint.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        jwk = {"kty": "RSA", "use": "sig", "alg": "RS256", "kid": kid, "n": n, "e": e}
        return cls(key, kid, jwk)

    def jwks(self) -> dict[str, Any]:
        return {"keys": [self.public_jwk]}


def generate_pem() -> bytes:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def load_signing_key(
    pem: str | None,
    path: str,
    generate: bool,
) -> SigningKey:
    """The key from ``pem``, or from the file at ``path``, made there first
    when missing and ``generate`` is set."""
    if pem:
        return SigningKey.from_pem(pem.encode())

    file = Path(path)
    if not file.exists():
        if not generate:
            raise RuntimeError(
                f"no JWT signing key: set JWT_PRIVATE_KEY or create {file}"
            )
        file.parent.mkdir(parents=True, exist_ok=True)
        try:
            # O_EXCL: several workers starting together make one key
            fd = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(fd, "wb") as out:
                out.write(generate_pem())
            log.warning("made a new JWT signing key in %s", file)

    return SigningKey.from_pem(file.read_bytes())
