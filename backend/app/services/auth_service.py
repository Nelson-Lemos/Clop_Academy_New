from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import hash_password, normalize_email, verify_password
from app.models.user import StudentProfile, User, UserRole, UserStatus


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == normalize_email(email)).first()
    if user is None:
        return None
    if user.estado != UserStatus.ACTIVE:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == normalize_email(email)).first()


def create_student(
    db: Session,
    *,
    nome_completo: str,
    email: str,
    password: str,
    telefone: str | None = None,
    aceite_termos: bool = False,
    profile_data: dict | None = None,
) -> User:
    """Cria um utilizador com perfil de aluno."""
    user = User(
        nome_completo=nome_completo.strip(),
        email=normalize_email(email),
        telefone=(telefone or "").strip() or None,
        password_hash=hash_password(password),
        role=UserRole.STUDENT,
        estado=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()

    profile = StudentProfile(user_id=user.id, **(profile_data or {}))
    db.add(profile)
    db.flush()
    return user
