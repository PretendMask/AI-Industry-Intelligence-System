"""敏感字段加解密（Fernet）。"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from ai_intelligence_system.utils.paths import fernet_key_path


def _load_or_create_key() -> bytes:
    path = fernet_key_path()
    if path.exists():
        return path.read_bytes().strip()
    key = Fernet.generate_key()
    path.write_bytes(key)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return key


def encrypt_secret(plain: str) -> str:
    if not plain:
        return ""
    f = Fernet(_load_or_create_key())
    return f.encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_secret(token: str) -> str:
    if not token:
        return ""
    f = Fernet(_load_or_create_key())
    try:
        return f.decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken:
        return ""
