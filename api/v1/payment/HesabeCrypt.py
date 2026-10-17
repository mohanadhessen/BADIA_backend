"""AES-256-CBC helpers compatible with Hesabe's documented hex payload format."""

from urllib.parse import unquote

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class HesabeCrypt:
    @staticmethod
    def _validate_key_iv(key: str, iv_key: str) -> tuple[bytes, bytes]:
        key_bytes = key.encode("utf-8")
        iv_bytes = iv_key.encode("utf-8")
        if len(key_bytes) != 32:
            raise ValueError("Hesabe AES-256 encryption key must be exactly 32 bytes")
        if len(iv_bytes) != 16:
            raise ValueError("Hesabe AES-CBC IV must be exactly 16 bytes")
        return key_bytes, iv_bytes

    @staticmethod
    def encrypt(value: str, key: str, iv_key: str) -> str:
        key_bytes, iv_bytes = HesabeCrypt._validate_key_iv(key, iv_key)
        padder = padding.PKCS7(256).padder()
        padded = padder.update(value.encode("utf-8")) + padder.finalize()
        encryptor = Cipher(algorithms.AES(key_bytes), modes.CBC(iv_bytes)).encryptor()
        return (encryptor.update(padded) + encryptor.finalize()).hex()

    @staticmethod
    def decrypt(code: str, key: str, iv_key: str) -> str:
        key_bytes, iv_bytes = HesabeCrypt._validate_key_iv(key, iv_key)
        normalized = unquote(code.strip())
        try:
            encrypted = bytes.fromhex(normalized)
        except ValueError as exc:
            raise ValueError("Hesabe response must be a hexadecimal ciphertext") from exc
        if not encrypted or len(encrypted) % 16:
            raise ValueError("Hesabe ciphertext length must be a non-zero multiple of 16 bytes")
        decryptor = Cipher(algorithms.AES(key_bytes), modes.CBC(iv_bytes)).decryptor()
        padded = decryptor.update(encrypted) + decryptor.finalize()
        unpadder = padding.PKCS7(256).unpadder()
        try:
            plaintext = unpadder.update(padded) + unpadder.finalize()
            return plaintext.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError("Unable to decrypt or validate the Hesabe payload") from exc
