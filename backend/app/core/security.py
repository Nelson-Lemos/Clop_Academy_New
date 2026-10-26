import re
import secrets
import time
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

MIN_PASSWORD_LENGTH = 8
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(normalize_email(email)))


def validate_password_strength(password: str) -> list[str]:
    """Devolve a lista de problemas encontrados na palavra-passe (vazia = válida)."""
    problems: list[str] = []
    if len(password) < MIN_PASSWORD_LENGTH:
        problems.append(f"A palavra-passe deve ter pelo menos {MIN_PASSWORD_LENGTH} caracteres.")
    if not any(c.isalpha() for c in password):
        problems.append("A palavra-passe deve conter pelo menos uma letra.")
    if not any(c.isdigit() for c in password):
        problems.append("A palavra-passe deve conter pelo menos um número.")
    return problems


def create_access_token(
    subject: str | int, expires_minutes: int | None = None, extra: dict | None = None
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict = {"sub": str(subject), "exp": expire, "typ": TOKEN_TYPE_ACCESS}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: str | int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(subject), "exp": expire, "typ": TOKEN_TYPE_REFRESH}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return {}


def generate_public_code(prefix: str = "", length: int = 12) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    body = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}{body}" if prefix else body


class LoginAttemptLimiter:
    """Limitador de tentativas de autenticação em memória.

    Adequado para uma única instância. Em ambiente multi-instância deve ser
    substituído por um armazenamento partilhado (Redis), conforme documentado
    em docs/architecture.md.
    """

    def __init__(self, max_attempts: int, lock_minutes: int) -> None:
        self.max_attempts = max_attempts
        self.lock_seconds = lock_minutes * 60
        self._attempts: dict[str, list[float]] = {}

    def _prune(self, key: str) -> list[float]:
        now = time.time()
        window = now - self.lock_seconds
        attempts = [t for t in self._attempts.get(key, []) if t > window]
        if attempts:
            self._attempts[key] = attempts
        else:
            self._attempts.pop(key, None)
        return attempts

    def is_blocked(self, key: str) -> bool:
        return len(self._prune(key)) >= self.max_attempts

    def register_failure(self, key: str) -> None:
        self._attempts.setdefault(key, []).append(time.time())

    def reset(self, key: str) -> None:
        self._attempts.pop(key, None)


login_limiter = LoginAttemptLimiter(
    max_attempts=settings.LOGIN_MAX_ATTEMPTS,
    lock_minutes=settings.LOGIN_LOCK_MINUTES,
)
