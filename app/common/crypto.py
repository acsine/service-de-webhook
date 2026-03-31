import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config.settings import settings

def encrypt_secret(data: bytes, key: str) -> tuple[bytes, str]:
    """
    Encrypts data using AES-256-GCM.
    Returns (nonce + ciphertext, key_id)
    """
    master_key = base64.b64decode(key)
    aesgcm = AESGCM(master_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext, "v1"

def decrypt_secret(ciphertext_with_nonce: bytes, key: str) -> bytes:
    """
    Decrypts data using AES-256-GCM.
    """
    master_key = base64.b64decode(key)
    aesgcm = AESGCM(master_key)
    nonce = ciphertext_with_nonce[:12]
    ciphertext = ciphertext_with_nonce[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)
