from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.exceptions import InvalidTag
from Crypto.Cipher import AES, ChaCha20_Poly1305
from app.security.profiles import validate_profile
class CiphertextError(Exception): pass

def cipher(backend, algorithm, key, nonce):
    if backend != 'pycryptodome': raise ValueError('Unsupported backend')
    return AES.new(key,AES.MODE_GCM,nonce=nonce,mac_len=16) if algorithm.startswith('AES-') else ChaCha20_Poly1305.new(key=key,nonce=nonce)

def seal_bytes(backend, algorithm, key, nonce, data, aad):
    validate_profile(algorithm,key,nonce)
    if backend == 'cryptography':
        c=(AESGCM if algorithm.startswith('AES-') else ChaCha20Poly1305)(key).encrypt(nonce,data,aad)
        return c[:-16],c[-16:]
    c=cipher(backend,algorithm,key,nonce); c.update(aad)
    return c.encrypt_and_digest(data)

def open_bytes(backend, algorithm, key, nonce, ct, tag, aad):
    validate_profile(algorithm,key,nonce)
    if backend not in ('cryptography','pycryptodome'): raise ValueError('Unsupported backend')
    if len(tag)!=16: raise CiphertextError('Verification failed')
    try:
        if backend=='cryptography':
            return (AESGCM if algorithm.startswith('AES-') else ChaCha20Poly1305)(key).decrypt(nonce,ct+tag,aad)
        c=cipher(backend,algorithm,key,nonce); c.update(aad)
        return c.decrypt_and_verify(ct,tag)
    except (ValueError,InvalidTag) as exc: raise CiphertextError('Verification failed') from exc
