import hmac
import struct
import time
import base64
import hashlib

def generate_steam_guard_code(shared_secret_b64: str) -> str:
    """
    Генерирует 5-значный код Steam Guard.
    shared_secret_b64 — поле shared_secret из maFile (base64).
    """
    secret = base64.b64decode(shared_secret_b64)
    timestamp = int(time.time()) // 30
    msg = struct.pack(">Q", timestamp)
    h = hmac.new(secret, msg, hashlib.sha1).digest()
    start = h[19] & 0x0F
    code = struct.unpack(">I", h[start:start+4])[0] & 0x7FFFFFFF
    chars = "23456789BCDFGHJKMNPQRTVWXY"
    result = ""
    for _ in range(5):
        result += chars[code % len(chars)]
        code //= len(chars)
    return result