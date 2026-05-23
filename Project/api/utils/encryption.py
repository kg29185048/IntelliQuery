import os
from cryptography.fernet import Fernet
import base64
import hashlib

# Derive a 32-byte url-safe base64 encoded key from the JWT_SECRET
secret = os.getenv("JWT_SECRET", "super_secret_fallback_key")
key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
fernet = Fernet(key)

def encrypt_uri(uri: str) -> str:
    """Encrypts a database URI string."""
    if not uri:
        return uri
    return fernet.encrypt(uri.encode()).decode()

def decrypt_uri(encrypted_uri: str) -> str:
    """Decrypts a database URI string."""
    if not encrypted_uri:
        return encrypted_uri
    try:
        return fernet.decrypt(encrypted_uri.encode()).decode()
    except Exception:
        # Fallback if the data wasn't encrypted (e.g. legacy data)
        return encrypted_uri
