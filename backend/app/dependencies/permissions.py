"""Autorização por permissões, aplicada sempre no backend.

O frontend nunca é uma camada de segurança: cada rota protegida valida aqui
a permissão exigida. As permissões são atribuídas por função (role).
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import HTTPException, status

from app.dependencies.auth import CurrentUser
from app.models.user import User, UserRole

# ---------------------------------------------------------------------------
# Catálogo de permissões
# ---------------------------------------------------------------------------
PERM_CURSOS_VER = "cursos:ver"
PERM_CURSOS_GERIR = "cursos:gerir"
PERM_TURMAS_GERIR = "turmas:gerir"
PERM_ALUNOS_VER = "alunos:ver"
PERM_ALUNOS_GERIR = "alunos:gerir"
PERM_INSCRICOES_VER = "inscricoes:ver"
PERM_INSCRICOES_GERIR = "inscricoes:gerir"
PERM_PAGAMENTOS_VER = "pagamentos:ver"
PERM_PAGAMENTOS_GERIR = "pagamentos:gerir"
PERM_EDITORIAL_GERIR = "editorial:gerir"
PERM_EVENTOS_GERIR = "eventos:gerir"
PERM_CAMPANHAS_GERIR = "campanhas:gerir"
PERM_MERCADOS_GERIR = "mercados:gerir"
PERM_UTILIZADORES_GERIR = "utilizadores:gerir"
PERM_AUDITORIA_VER = "auditoria:ver"
PERM_RELATORIOS_VER = "relatorios:ver"
PERM_AVALIACOES_CORRIGIR = "avaliacoes:corrigir"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        PERM_CURSOS_VER,
        PERM_CURSOS_GERIR,
        PERM_TURMAS_GERIR,
        PERM_ALUNOS_VER,
        PERM_ALUNOS_GERIR,
        PERM_INSCRICOES_VER,
        PERM_INSCRICOES_GERIR,
        PERM_PAGAMENTOS_VER,
        PERM_PAGAMENTOS_GERIR,
        PERM_EDITORIAL_GERIR,
        PERM_EVENTOS_GERIR,
        PERM_CAMPANHAS_GERIR,
        PERM_MERCADOS_GERIR,
        PERM_UTILIZADORES_GERIR,
        PERM_AUDITORIA_VER,
        PERM_RELATORIOS_VER,
        PERM_AVALIACOES_CORRIGIR,
    }
)

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    UserRole.STUDENT: frozenset(),
    UserRole.INSTRUCTOR: frozenset(
        {
            PERM_CURSOS_VER,
            PERM_TURMAS_GERIR,
            PERM_ALUNOS_VER,
            PERM_AVALIACOES_CORRIGIR,
        }
    ),
    UserRole.EDITOR: frozenset(
        {
            PERM_CURSOS_VER,
            PERM_EDITORIAL_GERIR,
            PERM_EVENTOS_GERIR,
            PERM_CAMPANHAS_GERIR,
            PERM_RELATORIOS_VER,
        }
    ),
    UserRole.FINANCE: frozenset(
        {
            PERM_CURSOS_VER,
            PERM_ALUNOS_VER,
            PERM_INSCRICOES_VER,
            PERM_INSCRICOES_GERIR,
            PERM_PAGAMENTOS_VER,
            PERM_PAGAMENTOS_GERIR,
            PERM_RELATORIOS_VER,
        }
    ),
    UserRole.ADMIN: ALL_PERMISSIONS - {PERM_UTILIZADORES_GERIR, PERM_AUDITORIA_VER},
    UserRole.SUPERADMIN: ALL_PERMISSIONS,
}

STAFF_ROLES = (
    UserRole.INSTRUCTOR,
    UserRole.EDITOR,
    UserRole.FINANCE,
    UserRole.ADMIN,
    UserRole.SUPERADMIN,
)


def permissions_for(role: str) -> frozenset[str]:
    return ROLE_PERMISSIONS.get(role, frozenset())


def has_permission(user: User, permission: str) -> bool:
    return permission in permissions_for(user.role)


def is_staff(user: User) -> bool:
    return user.role in STAFF_ROLES


def require_permissions(*required: str) -> Callable:
    """Exige que o utilizador possua todas as permissões indicadas."""

    def checker(current_user: CurrentUser) -> User:
        granted = permissions_for(current_user.role)
        if not all(permission in granted for permission in required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para esta operação.",
            )
        return current_user

    return checker


def require_roles(*roles: str) -> Callable:
    def checker(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para esta operação.",
            )
        return current_user

    return checker


require_admin = require_roles(UserRole.ADMIN, UserRole.SUPERADMIN)
require_superadmin = require_roles(UserRole.SUPERADMIN)
require_staff = require_roles(*STAFF_ROLES)
