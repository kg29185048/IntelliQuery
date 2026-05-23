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
        # Check if the value looks like a plain URI (legacy unencrypted data)
        if encrypted_uri.startswith(("mongodb://", "mongodb+srv://", "postgresql", "mysql", "sqlite")):
            return encrypted_uri
        raise ValueError(
            "Unable to decrypt the database URI. "
            "This workspace was likely created on a server with a different JWT_SECRET. "
            "Ask the workspace admin to re-create the workspace on this server."
        )

