"""Password hashing and session-token helpers (standard library only).

Avoids third-party crypto dependencies for the MVP: passwords use PBKDF2-HMAC-
SHA256, and session tokens are random and stored only as SHA-256 hashes.
"""
import hashlib
import hmac
import os
import secrets

_ITERATIONS = 200_000
_ALGO = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    """Return a self-describing hash: ``algo$iterations$salt_hex$hash_hex``."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"{_ALGO}${_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time verification of a password against a stored hash."""
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$")
        if algo != _ALGO:
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def new_session_token() -> str:
    """A URL-safe random token handed to the client (never stored raw)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """SHA-256 of a session token, as stored in the database."""
    return hashlib.sha256(token.encode()).hexdigest()
