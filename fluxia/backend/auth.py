import hashlib
import hmac
import os
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = os.environ.get("FLUXIA_SECRET", "fluxia-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 72


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${h}"


def verify_password(plain: str, hashed: str) -> bool:
    if "$" not in hashed:
        return False
    salt, h = hashed.split("$", 1)
    return hmac.compare_digest(hashlib.sha256((salt + plain).encode()).hexdigest(), h)


def create_token(account_id: int, email: str, role: str = "admin") -> str:
    expires = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": str(account_id), "email": email, "role": role, "exp": expires},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None
