import base64

from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.config import settings


def _get_fernet_key() -> bytes:
    """
    Get the master encryption key from settings.
    Fernet requires a url-safe base64-encoded 32-byte key.
    If the provided key is not the right format, we try to format it.
    """
    raw_key = (
        settings.encryption_key.get_secret_value()
        if isinstance(settings.encryption_key, SecretStr)
        else settings.encryption_key
    )

    # In a real production system, ensure ENCRYPTION_KEY is exactly a 32-url-safe-base64-encoded string.
    # For dev fallback, pad/truncate to 32 bytes and b64 encode
    if len(raw_key) != 44 or not raw_key.endswith("="):
        # Hash it or pad it to 32 bytes
        padded = (raw_key.encode("utf-8") + b"0" * 32)[:32]
        return base64.urlsafe_b64encode(padded)

    return raw_key.encode("utf-8")


def encrypt_key(plaintext: str) -> str:
    """Encrypt a string using symmetric AES128 (Fernet)."""
    if not plaintext:
        return ""

    f = Fernet(_get_fernet_key())
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_key(ciphertext: str) -> str:
    """Decrypt a string using symmetric AES128 (Fernet)."""
    if not ciphertext:
        return ""

    f = Fernet(_get_fernet_key())
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
