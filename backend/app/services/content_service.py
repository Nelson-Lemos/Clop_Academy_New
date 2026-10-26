from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.content import Article, ArticleStatus


def publicar_agendados(db: Session) -> int:
    """Publica artigos cujo agendamento já chegou.

    Executado no arranque da aplicação e disponível para execução manual.
    """
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    pendentes = (
        db.query(Article)
        .filter(
            Article.estado == ArticleStatus.AGENDADO,
            Article.agendado_para.isnot(None),
            Article.agendado_para <= agora,
        )
        .all()
    )

    for artigo in pendentes:
        artigo.estado = ArticleStatus.PUBLICADO
        artigo.publicado_em = artigo.publicado_em or agora

    if pendentes:
        db.commit()
    return len(pendentes)
