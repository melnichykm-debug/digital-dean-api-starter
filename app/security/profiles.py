"""Параметри визначеного навчального профілю, не універсальні межі схем."""

KEY_BYTES = {
    "AES-128-GCM": 16,
    "AES-256-GCM": 32,
    "ChaCha20-Poly1305": 32,
}
BACKENDS = ("cryptography", "pycryptodome")
NONCE_BYTES = 12
TAG_BYTES = 16


def validate_profile(algorithm, key, nonce):
    if algorithm not in KEY_BYTES or not isinstance(key,bytes) or len(key)!=KEY_BYTES[algorithm] or not isinstance(nonce,bytes) or len(nonce)!=12:
        raise ValueError('Invalid cipher profile')
