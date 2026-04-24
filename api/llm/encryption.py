"""Fernet wrapper used to encrypt LLM API keys at rest."""
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from config import get_settings


def _fernet() -> Fernet:
    return Fernet(get_settings().ranger_encryption_key.encode())


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as e:
        raise RuntimeError(
            "Failed to decrypt API key — RANGER_ENCRYPTION_KEY likely changed since it was stored."
        ) from e


def last4(plaintext: str) -> str:
    return plaintext[-4:] if len(plaintext) >= 4 else plaintext
