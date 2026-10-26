from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.institution import institution
from app.core.utils import PageMeta, PaginatedResponse, page_params, slugify
from app.models.catalog import Course, CourseStatus, Enrollment, EnrollmentStatus
from app.models.content import (
    Article,
    ArticleStatus,
    Campaign,
    CampaignStatus,
    Category,
    Event,
    EventRegistration,
    EventStatus,
    Project,
)
from app.models.messaging import (
    AuditAction,
    ContactMessage,
    ContactMessageStatus,
    NewsletterSubscription,
)
from app.models.user import User
from app.schemas.common import (
    ContactMessageCreate,
    InstitutionOut,
    MessageOut,
    NewsletterCreate,
)
from app.schemas.content import (
    ArticleDetailOut,
    ArticleOut,
    CampaignOut,
    EventDetailOut,
    EventOut,
    EventRegistrationCreate,
    ProjectOut,
)
from app.schemas.catalog import CourseDetailOut, CourseOut
from app.services import market_service
from app.services.audit_service import log_audit
from app.services.course_service import to_course_detail, to_course_out

router = APIRouter(prefix="/public", tags=["portal público"])


def _agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _article_out(article: Article) -> ArticleOut:
    conteudo = article.conteudo or ""
    palavras = len(conteudo.split())
    return ArticleOut(
        id=article.id,
        titulo=article.titulo,
        slug=article.slug,
        resumo=article.resumo,
        imagem_url=article.imagem_url,
        tipo=article.tipo,
        categoria_nome=article.categoria.nome if article.categoria else None,
        categoria_slug=article.categoria.slug if article.categoria else None,
        autor_nome=article.autor_nome
        or (article.autor.nome_completo if article.autor else None),
        publicado_em=article.publicado_em,
        leitura_minutos=max(1, round(palavras / 200)),
    )


def _event_out(event: Event) -> EventOut:
    ocupados = (
        event.inscricoes
        if event.inscricoes is not None
        else []
    )
    lugares = None
    if event.vagas:
        lugares = max(0, event.vagas - len(ocupados))
    return EventOut(
        id=event.id,
        titulo=event.titulo,
        slug=event.slug,
        resumo=event.resumo,
        imagem_url=event.imagem_url,
        local=event.local,
        cidade=event.cidade,
        inicio=event.inicio,
        fim=event.fim,
        formato=event.formato,
        vagas=event.vagas,
        inscricoes_abertas=event.inscricoes_abertas,
        requer_inscricao=event.requer_inscricao,
        estado=event.estado,
        categoria_nome=event.categoria.nome if event.categoria else None,
        lugares_disponiveis=lugares,
    )


# ---------------------------------------------------------------------------
# Identidade institucional
# ---------------------------------------------------------------------------
@router.get("/instituicao", response_model=InstitutionOut)
def instituicao() -> InstitutionOut:
    """Identidade e contactos institucionais (fonte única de verdade)."""
    return InstitutionOut(
        nome=institution.nome,
        area=institution.area,
        assinatura=institution.assinatura,
        slogan=institution.slogan,
        missao=institution.missao,
        visao=institution.visao,
        valores=list(institution.valores),
        areas_actuacao=[dict(a) for a in institution.areas_actuacao],
        morada=institution.morada,
        unitel=institution.unitel,
        africell=institution.africell,
        email=institution.email,
        cidade=institution.cidade,
        pais=institution.pais,
        redes_sociais=institution.social,
    )


# ---------------------------------------------------------------------------
# Página inicial
# ---------------------------------------------------------------------------
@router.get("/home")
def home(db: Session = Depends(get_db)) -> dict:
    """Dados agregados da página inicial institucional."""
    cursos = (
        db.query(Course)
        .filter(Course.estado == CourseStatus.PUBLISHED)
        .order_by(Course.created_at.desc())
        .limit(6)
        .all()
    )

    artigos = (
        db.query(Article)
        .filter(Article.estado == ArticleStatus.PUBLICADO)
        .order_by(
            func.isnull(Article.publicado_em).asc(),
            Article.publicado_em.desc(),
        )
        .limit(6)
        .all()
    )

    eventos = (
        db.query(Event)
        .filter(Event.estado == EventStatus.PUBLICADO, Event.inicio >= _agora())
        .order_by(Event.inicio)
        .limit(6)
        .all()
    )

    campanhas = (
        db.query(Campaign)
        .filter(
            Campaign.estado.in_(
                [CampaignStatus.EM_CURSO, CampaignStatus.PLANEADA]
            ),
            Campaign.destaque_home.is_(True),
        )
        .order_by(Campaign.created_at.desc())
        .limit(3)
        .all()
    )

    projectos = (
        db.query(Project).order_by(Project.nome).limit(12).all()
    )

    return {
        "cursos": [to_course_out(db, c) for c in cursos],
        "artigos": [_article_out(a) for a in artigos],
        "eventos": [_event_out(e) for e in eventos],
        "campanhas": [CampaignOut.model_validate(c) for c in campanhas],
        "projectos": [ProjectOut.model_validate(p) for p in projectos],
        "mercados": market_service.overview(db),
    }


# ---------------------------------------------------------------------------
# Catálogo de cursos
# ---------------------------------------------------------------------------
@router.get("/cursos", response_model=PaginatedResponse[CourseOut])
def listar_cursos(
    db: Session = Depends(get_db),
    params=Depends(page_params),
    q: str | None = Query(default=None, max_length=120),
    area: str | None = Query(default=None, max_length=80),
    modalidade: str | None = Query(default=None, max_length=20),
    nivel: str | None = Query(default=None, max_length=20),
    somente_abertos: bool = Query(default=False),
) -> PaginatedResponse[CourseOut]:
    query = db.query(Course).filter(Course.estado == CourseStatus.PUBLISHED)

    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Course.nome.ilike(termo),
                Course.descricao_resumida.ilike(termo),
                Course.descricao.ilike(termo),
            )
        )
    if area:
        query = query.filter(Course.area == area)
    if modalidade:
        query = query.filter(Course.modalidade == modalidade)
    if nivel:
        query = query.filter(Course.nivel == nivel)
    if somente_abertos:
        query = query.filter(Course.inscricoes_abertas.is_(True))

    total = query.count()
    cursos = (
        query.order_by(Course.created_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
        .all()
    )

    return PaginatedResponse(
        items=[to_course_out(db, c) for c in cursos],
        meta=PageMeta.build(
            page=params.page, page_size=params.page_size, total=total
        ),
    )


@router.get("/cursos/{slug}", response_model=CourseDetailOut)
def detalhe_curso(slug: str, db: Session = Depends(get_db)) -> CourseDetailOut:
    curso = (
        db.query(Course)
        .filter(Course.slug == slug, Course.estado == CourseStatus.PUBLISHED)
        .first()
    )
    if curso is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Curso não encontrado."
        )
    return to_course_detail(db, curso)


# ---------------------------------------------------------------------------
# Notícias e análises
# ---------------------------------------------------------------------------
@router.get("/artigos", response_model=PaginatedResponse[ArticleOut])
def listar_artigos(
    db: Session = Depends(get_db),
    params=Depends(page_params),
    q: str | None = Query(default=None, max_length=120),
    categoria: str | None = Query(default=None, max_length=120),
    tipo: str | None = Query(default=None, max_length=20),
) -> PaginatedResponse[ArticleOut]:
    query = db.query(Article).filter(Article.estado == ArticleStatus.PUBLICADO)

    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Article.titulo.ilike(termo),
                Article.resumo.ilike(termo),
                Article.conteudo.ilike(termo),
            )
        )
    if categoria:
        query = query.join(Category, Article.categoria_id == Category.id).filter(
            Category.slug == categoria
        )
    if tipo:
        query = query.filter(Article.tipo == tipo)

    total = query.count()
    artigos = (
        query.order_by(
            func.isnull(Article.publicado_em).asc(),
            Article.publicado_em.desc(),
            Article.id.desc(),
        )
        .offset(params.offset)
        .limit(params.page_size)
        .all()
    )

    return PaginatedResponse(
        items=[_article_out(a) for a in artigos],
        meta=PageMeta.build(
            page=params.page, page_size=params.page_size, total=total
        ),
    )


@router.get("/artigos/{slug}", response_model=ArticleDetailOut)
def detalhe_artigo(slug: str, db: Session = Depends(get_db)) -> ArticleDetailOut:
    artigo = (
        db.query(Article)
        .filter(Article.slug == slug, Article.estado == ArticleStatus.PUBLICADO)
        .first()
    )
    if artigo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artigo não encontrado."
        )

    artigo.visualizacoes = (artigo.visualizacoes or 0) + 1
    db.commit()
    db.refresh(artigo)

    return ArticleDetailOut(
        **_article_out(artigo).model_dump(),
        conteudo=artigo.conteudo,
        fonte=artigo.fonte,
        fonte_url=artigo.fonte_url,
        tags=artigo.tags,
        estado=artigo.estado,
        visualizacoes=artigo.visualizacoes,
        atualizado_em=artigo.updated_at,
    )


@router.get("/categorias")
def listar_categorias(db: Session = Depends(get_db)) -> list[dict]:
    categorias = db.query(Category).order_by(Category.nome).all()
    return [
        {
            "id": c.id,
            "nome": c.nome,
            "slug": c.slug,
            "descricao": c.descricao,
            "cor": c.cor,
        }
        for c in categorias
    ]


# ---------------------------------------------------------------------------
# Actividades e eventos
# ---------------------------------------------------------------------------
@router.get("/eventos", response_model=PaginatedResponse[EventOut])
def listar_eventos(
    db: Session = Depends(get_db),
    params=Depends(page_params),
    q: str | None = Query(default=None, max_length=120),
    incluir_passados: bool = Query(default=False),
) -> PaginatedResponse[EventOut]:
    query = db.query(Event).filter(Event.estado == EventStatus.PUBLICADO)

    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(or_(Event.titulo.ilike(termo), Event.resumo.ilike(termo)))
    if not incluir_passados:
        query = query.filter(Event.inicio >= _agora())

    total = query.count()
    eventos = (
        query.order_by(Event.inicio).offset(params.offset).limit(params.page_size).all()
    )

    return PaginatedResponse(
        items=[_event_out(e) for e in eventos],
        meta=PageMeta.build(
            page=params.page, page_size=params.page_size, total=total
        ),
    )


@router.get("/eventos/{slug}", response_model=EventDetailOut)
def detalhe_evento(slug: str, db: Session = Depends(get_db)) -> EventDetailOut:
    evento = (
        db.query(Event)
        .filter(Event.slug == slug, Event.estado == EventStatus.PUBLICADO)
        .first()
    )
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado."
        )
    return EventDetailOut(**_event_out(evento).model_dump(), descricao=evento.descricao)


@router.post("/eventos/{event_id}/inscricao", response_model=MessageOut)
def inscrever_evento(
    event_id: int,
    payload: EventRegistrationCreate,
    db: Session = Depends(get_db),
    request: Request = None,
) -> MessageOut:
    """Regista inscrição num evento (público, com ou sem conta)."""
    evento = (
        db.query(Event)
        .filter(Event.id == event_id, Event.estado == EventStatus.PUBLICADO)
        .first()
    )
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado."
        )
    if not evento.requer_inscricao:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este evento não requer inscrição prévia.",
        )
    if not evento.inscricoes_abertas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="As inscrições para este evento estão encerradas.",
        )
    if evento.vagas and len(evento.inscricoes) >= evento.vagas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não existem lugares disponíveis para este evento.",
        )

    email = payload.email.strip().lower()
    ja_inscrito = (
        db.query(EventRegistration)
        .filter(
            EventRegistration.event_id == evento.id,
            EventRegistration.email == email,
        )
        .first()
    )
    if ja_inscrito is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma inscrição com este e-mail para o evento.",
        )

    inscricao = EventRegistration(
        event_id=evento.id,
        nome=payload.nome.strip(),
        email=email,
        telefone=payload.telefone,
        notas=payload.notas,
    )
    db.add(inscricao)
    log_audit(
        db,
        action=AuditAction.REGISTO,
        entity="event_registration",
        entity_id=evento.id,
        detalhe=f"Inscrição pública no evento «{evento.titulo}».",
        request=request,
    )
    db.commit()

    return MessageOut(
        mensagem="Inscrição registada com sucesso.",
        detalhe=(
            "A tua inscrição foi registada. A equipa CLOP entrará em contacto "
            "com os detalhes do evento."
        ),
    )


# ---------------------------------------------------------------------------
# Projectos e campanhas
# ---------------------------------------------------------------------------
@router.get("/projectos", response_model=list[ProjectOut])
def listar_projectos(db: Session = Depends(get_db)) -> list[ProjectOut]:
    projectos = db.query(Project).order_by(Project.nome).all()
    return [ProjectOut.model_validate(p) for p in projectos]


@router.get("/campanhas", response_model=list[CampaignOut])
def listar_campanhas(db: Session = Depends(get_db)) -> list[CampaignOut]:
    agora = _agora()
    campanhas = (
        db.query(Campaign)
        .filter(Campaign.estado.in_([CampaignStatus.EM_CURSO, CampaignStatus.PLANEADA]))
        .all()
    )
    activas = [
        c
        for c in campanhas
        if (c.data_inicio is None or c.data_inicio <= agora)
        and (c.data_fim is None or c.data_fim >= agora)
    ]
    return [CampaignOut.model_validate(c) for c in activas]


@router.post("/campanhas/{campaign_id}/clique")
def registar_clique(campaign_id: int, db: Session = Depends(get_db)) -> dict:
    campanha = db.get(Campaign, campaign_id)
    if campanha is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campanha não encontrada."
        )
    campanha.cliques = (campanha.cliques or 0) + 1
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Contactos e newsletter
# ---------------------------------------------------------------------------
@router.post("/contactos", response_model=MessageOut)
def contacto_institucional(
    payload: ContactMessageCreate,
    db: Session = Depends(get_db),
    request: Request = None,
) -> MessageOut:
    mensagem = ContactMessage(
        nome=payload.nome.strip(),
        email=payload.email.strip().lower(),
        telefone=payload.telefone,
        assunto=payload.assunto.strip(),
        categoria=payload.categoria,
        mensagem=payload.mensagem.strip(),
    )
    db.add(mensagem)
    db.flush()
    log_audit(
        db,
        action=AuditAction.CONTACTO_RECEBIDO,
        entity="contact_message",
        entity_id=mensagem.id,
        detalhe=f"Pedido de contacto: {payload.assunto}",
        request=request,
    )
    db.commit()
    return MessageOut(
        mensagem="Mensagem recebida.",
        detalhe="A nossa equipa responderá através do e-mail ou telefone indicados.",
    )


@router.post("/newsletter", response_model=MessageOut)
def subscrever_newsletter(
    payload: NewsletterCreate,
    db: Session = Depends(get_db),
    request: Request = None,
) -> MessageOut:
    if not payload.consentimento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="É necessário aceitar a política de privacidade para subscrever.",
        )

    email = payload.email.strip().lower()
    existente = (
        db.query(NewsletterSubscription)
        .filter(NewsletterSubscription.email == email)
        .first()
    )
    if existente is not None:
        if existente.confirmado:
            return MessageOut(
                mensagem="Já está subscrito.",
                detalhe="Este e-mail já consta da nossa lista de subscritores.",
            )
        existente.consentimento = True
        existente.nome = payload.nome or existente.nome
        db.commit()
        return MessageOut(
            mensagem="Subscrição registada.",
            detalhe="Confirme a subscrição através do link enviado para o seu e-mail.",
        )

    subscricao = NewsletterSubscription(
        email=email,
        nome=payload.nome,
        consentimento=True,
        origem=payload.origem,
    )
    db.add(subscricao)
    log_audit(
        db,
        action=AuditAction.NEWSLETTER,
        entity="newsletter_subscription",
        detalhe="Nova subscrição da newsletter.",
        request=request,
    )
    db.commit()
    return MessageOut(
        mensagem="Subscrição registada.",
        detalhe="Confirme a subscrição através do link enviado para o seu e-mail.",
    )


# ---------------------------------------------------------------------------
# Mercados financeiros
# ---------------------------------------------------------------------------
@router.get("/mercados")
def mercados(
    db: Session = Depends(get_db),
    mercado: str | None = Query(default=None, max_length=20),
) -> dict:
    """Informação de mercados com origem, data e estado de actualização."""
    overview = market_service.overview(db, mercado=mercado)
    return overview.model_dump(mode="json")


@router.get("/mercados/fontes")
def fontes_mercados(db: Session = Depends(get_db)) -> dict:
    return {
        "fontes": [f.model_dump(mode="json") for f in market_service.status_fontes()]
    }


# ---------------------------------------------------------------------------
# Verificação pública de certificados
# ---------------------------------------------------------------------------
@router.get("/certificados/{codigo}")
def verificar_certificado(codigo: str, db: Session = Depends(get_db)) -> dict:
    """Verificação pública de um certificado.

    Revela apenas os dados estritamente necessários à validação.
    """
    from app.schemas.enrollment import CertificatePublicOut
    from app.services.certificate_service import verificar_certificado as _verificar

    certificado = _verificar(db, codigo)
    if certificado is None:
        return CertificatePublicOut(
            codigo=codigo.strip().upper(), valido=False, estado="NAO_ENCONTRADO"
        ).model_dump(mode="json")

    return CertificatePublicOut(
        codigo=certificado.codigo,
        valido=certificado.estado == "EMITIDO",
        estado=certificado.estado,
        aluno_nome=certificado.user.nome_completo if certificado.user else None,
        curso_nome=certificado.curso.nome if certificado.curso else None,
        emitido_em=certificado.emitido_em,
        nota_final=certificado.nota_final,
    ).model_dump(mode="json")
