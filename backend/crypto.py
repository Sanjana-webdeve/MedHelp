# crypto.py
from cryptography.fernet import Fernet

# generate key once and store securely (example: env var or KMS)
# key = Fernet.generate_key()
# store key safely — DO NOT hardcode in production
def load_key_from_env():
    import os
    k = os.environ.get("FERNET_KEY")
    if not k:
        raise RuntimeError("FERNET_KEY not set")
    return k.encode()

def encrypt_bytes(plaintext_bytes):
    key = load_key_from_env()
    f = Fernet(key)
    return f.encrypt(plaintext_bytes)

def decrypt_bytes(cipher_bytes):
    key = load_key_from_env()
    f = Fernet(key)
    return f.decrypt(cipher_bytes)
