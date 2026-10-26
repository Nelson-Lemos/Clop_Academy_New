from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.core.utils import PageMeta, PaginatedResponse, page_params, slugify
from app.dependencies.auth import CurrentUser
from app.dependencies.permissions import (
    PERM_CAMPANHAS_GERIR,
    PERM_EDITORIAL_GERIR,
    PERM_EVENTOS_GERIR,
    require_permissions,
)
from app.models.content import (
    Advertisement,
    Article,
    ArticleStatus,
    Campaign,
    Category,
    Event,
    EventRegistration,
    EventStatus,
    Project,
)
from app.models.messaging import AuditAction
from app.schemas.common import MessageOut
from app.schemas.content import (
    AdvertisementCreate,
    AdvertisementOut,
    ArticleCreate,
    ArticleDetailOut,
    ArticleUpdate,
    CampaignAdminOut,
    CampaignCreate,
    CampaignUpdate,
    CategoryCreate,
    CategoryOut,
    EventCreate,
    EventDetailOut,
    EventUpdate,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
)
from app.services.audit_service import log_audit

router = APIRouter(prefix="/admin", tags=["administração — editorial"])


def _agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _slug_unico(db: Session, modelo, base: str) -> str:
    slug = slugify(base)
    candidato = slug
    sufixo = 2
    while db.query(modelo).filter(modelo.slug == candidato).first():
        candidato = f"{slug}-{sufixo}"
        sufixo += 1
    return candidato


# ---------------------------------------------------------------------------
# Categorias
# ---------------------------------------------------------------------------
@router.get("/categorias", response_model=list[CategoryOut])
def listar_categorias_admin(
    current_user: User = Depends(require_permissions(PERM_EDITORIAL_GERIR)),
    db: Session = Depends(get_db),
) -> list[CategoryOut]:
    categorias = db.query(Category).order_by(Category.nome).all()
    return [CategoryOut.model_validate(c) for c in categorias]


@router.post("/categorias", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def criar_categoria(
    payload: CategoryCreate,
    current_user: User = Depends(require_permissions(PERM_EDITORIAL_GERIR)),
    db: Session = Depends(get_db),
) -> CategoryOut:
    slug = payload.slug or _slug_unico(db, Category, payload.nome)
    categoria = Category(
        nome=payload.nome,
        slug=slug,
        descricao=payload.descricao,
        cor=payload.cor,
    )
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return CategoryOut.model_validate(categoria)


# ---------------------------------------------------------------------------
# Artigos
# ---------------------------------------------------------------------------
@router.get("/artigos", response_model=PaginatedResponse[ArticleDetailOut])
def listar_artigos_admin(
    current_user: User = Depends(require_permissions(PERM_EDITORIAL_GERIR)),
    db: Session = Depends(get_db),
    params=Depends(page_params),
    q: str | None = Query(default=None, max_length=120),
    estado: str | None = Query(default=None, max_length=20),
    tipo: str | None = Query(default=None, max_length=20),
) -> PaginatedResponse[ArticleDetailOut]:
    query = db.query(Article)
    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(or_(Article.titulo.ilike(termo), Article.resumo.ilike(termo)))
    if estado:
        query = query.filter(Article.estado == estado)
    if tipo:
        query = query.filter(Article.tipo == tipo)

    total = query.count()
    artigos = (
        query.order_by(Article.updated_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
        .all()
    )

    items = []
    for artigo in artigos:
        items.append(
            ArticleDetailOut(
                id=artigo.id,
                titulo=artigo.titulo,
                slug=artigo.slug,
                resumo=artigo.resumo,
                conteudo=artigo.conteudo,
                imagem_url=artigo.imagem_url,
                tipo=artigo.tipo,
                categoria_nome=artigo.categoria.nome if artigo.categoria else None,
                categoria_slug=artigo.categoria.slug if artigo.categoria else None,
                autor_nome=artigo.autor_nome
                or (artigo.autor.nome_completo if artigo.autor else None),
                publicado_em=artigo.publicado_em,
                leitura_minutos=max(1, round(len((artigo.conteudo or "").split()) / 200)),
                fonte=artigo.fonte,
                fonte_url=artigo.fonte_url,
                tags=artigo.tags,
                estado=artigo.estado,
                visualizacoes=artigo.visualizacoes,
                atualizado_em=artigo.updated_at,
            )
        )

    return PaginatedResponse(
        items=items,
        meta=PageMeta.build(page=params.page, page_size=params.page_size, total=total),
    )


@router.post("/artigos", response_model=ArticleDetailOut, status_code=status.HTTP_201_CREATED)
def criar_artigo(
    payload: ArticleCreate,
    current_user: User = Depends(require_permissions(PERM_EDITORIAL_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> ArticleDetailOut:
    dados = payload.model_dump()
    slug = dados.pop("slug", None) or _slug_unico(db, Article, dados["titulo"])

    if dados.get("estado") == ArticleStatus.PUBLICADO and not dados.get("publicado_em"):
        dados["publicado_em"] = _agora()

    artigo = Article(slug=slug, **dados)
    db.add(artigo)
    db.flush()
    log_audit(
        db,
        action=AuditAction.CRIAR_ARTIGO,
        user_id=current_user.id,
        entity="article",
        entity_id=artigo.id,
        detalhe=f"Criação do artigo «{artigo.titulo}».",
        request=request,
    )
    db.commit()
    db.refresh(artigo)
    return _detalhe(artigo)


def _detalhe(artigo: Article) -> ArticleDetailOut:
    return ArticleDetailOut(
        id=artigo.id,
        titulo=artigo.titulo,
        slug=artigo.slug,
        resumo=artigo.resumo,
        conteudo=artigo.conteudo,
        imagem_url=artigo.imagem_url,
        tipo=artigo.tipo,
        categoria_nome=artigo.categoria.nome if artigo.categoria else None,
        categoria_slug=artigo.categoria.slug if artigo.categoria else None,
        autor_nome=artigo.autor_nome
        or (artigo.autor.nome_completo if artigo.autor else None),
        publicado_em=artigo.publicado_em,
        leitura_minutos=max(1, round(len((artigo.conteudo or "").split()) / 200)),
        fonte=artigo.fonte,
        fonte_url=artigo.fonte_url,
        tags=artigo.tags,
        estado=artigo.estado,
        visualizacoes=artigo.visualizacoes,
        atualizado_em=artigo.updated_at,
    )


@router.get("/artigos/{article_id}", response_model=ArticleDetailOut)
def detalhe_artigo_admin(
    article_id: int,
    current_user: User = Depends(require_permissions(PERM_EDITORIAL_GERIR)),
    db: Session = Depends(get_db),
) -> ArticleDetailOut:
    artigo = db.get(Article, article_id)
    if artigo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artigo não encontrado."
        )
    return _detalhe(artigo)


@router.put("/artigos/{article_id}", response_model=ArticleDetailOut)
def actualizar_artigo(
    article_id: int,
    payload: ArticleUpdate,
    current_user: User = Depends(require_permissions(PERM_EDITORIAL_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> ArticleDetailOut:
    artigo = db.get(Article, article_id)
    if artigo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artigo não encontrado."
        )

    dados = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(artigo, campo, valor)

    if artigo.estado == ArticleStatus.PUBLICADO and not artigo.publicado_em:
        artigo.publicado_em = _agora()

    log_audit(
        db,
        action=AuditAction.ATUALIZAR_ARTIGO,
        user_id=current_user.id,
        entity="article",
        entity_id=artigo.id,
        request=request,
    )
    db.commit()
    db.refresh(artigo)
    return _detalhe(artigo)


@router.post("/artigos/{article_id}/publicar", response_model=ArticleDetailOut)
def publicar_artigo(
    article_id: int,
    current_user: User = Depends(require_permissions(PERM_EDITORIAL_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> ArticleDetailOut:
    artigo = db.get(Article, article_id)
    if artigo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artigo não encontrado."
        )
    artigo.estado = ArticleStatus.PUBLICADO
    artigo.publicado_em = artigo.publicado_em or _agora()
    log_audit(
        db,
        action=AuditAction.PUBLICAR_ARTIGO,
        user_id=current_user.id,
        entity="article",
        entity_id=artigo.id,
        detalhe="Publicação de artigo.",
        request=request,
    )
    db.commit()
    db.refresh(artigo)
    return _detalhe(artigo)


@router.delete("/artigos/{article_id}", response_model=MessageOut)
def arquivar_artigo(
    article_id: int,
    current_user: User = Depends(require_permissions(PERM_EDITORIAL_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> MessageOut:
    artigo = db.get(Article, article_id)
    if artigo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artigo não encontrado."
        )
    artigo.estado = ArticleStatus.ARQUIVADO
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_ARTIGO,
        user_id=current_user.id,
        entity="article",
        entity_id=artigo.id,
        detalhe="Arquivamento de artigo.",
        request=request,
    )
    db.commit()
    return MessageOut(mensagem="Artigo arquivado.")


# ---------------------------------------------------------------------------
# Eventos
# ---------------------------------------------------------------------------
@router.get("/eventos", response_model=PaginatedResponse[EventDetailOut])
def listar_eventos_admin(
    current_user: User = Depends(require_permissions(PERM_EVENTOS_GERIR)),
    db: Session = Depends(get_db),
    params=Depends(page_params),
    estado: str | None = Query(default=None, max_length=20),
) -> PaginatedResponse[EventDetailOut]:
    query = db.query(Event)
    if estado:
        query = query.filter(Event.estado == estado)

    total = query.count()
    eventos = (
        query.order_by(Event.inicio.desc())
        .offset(params.offset)
        .limit(params.page_size)
        .all()
    )

    items = []
    for evento in eventos:
        lugares = (
            max(0, evento.vagas - len(evento.inscricoes)) if evento.vagas else None
        )
        items.append(
            EventDetailOut(
                id=evento.id,
                titulo=evento.titulo,
                slug=evento.slug,
                resumo=evento.resumo,
                descricao=evento.descricao,
                imagem_url=evento.imagem_url,
                local=evento.local,
                cidade=evento.cidade,
                inicio=evento.inicio,
                fim=evento.fim,
                formato=evento.formato,
                vagas=evento.vagas,
                inscricoes_abertas=evento.inscricoes_abertas,
                requer_inscricao=evento.requer_inscricao,
                estado=evento.estado,
                categoria_nome=evento.categoria.nome if evento.categoria else None,
                lugares_disponiveis=lugares,
            )
        )

    return PaginatedResponse(
        items=items,
        meta=PageMeta.build(page=params.page, page_size=params.page_size, total=total),
    )


@router.post("/eventos", response_model=EventDetailOut, status_code=status.HTTP_201_CREATED)
def criar_evento(
    payload: EventCreate,
    current_user: User = Depends(require_permissions(PERM_EVENTOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> EventDetailOut:
    dados = payload.model_dump()
    slug = dados.pop("slug", None) or _slug_unico(db, Event, dados["titulo"])
    evento = Event(slug=slug, **dados)
    db.add(evento)
    db.flush()
    log_audit(
        db,
        action=AuditAction.CRIAR_EVENTO,
        user_id=current_user.id,
        entity="event",
        entity_id=evento.id,
        detalhe=f"Criação do evento «{evento.titulo}».",
        request=request,
    )
    db.commit()
    db.refresh(evento)
    return _evento_out(evento)


def _evento_out(evento: Event) -> EventDetailOut:
    lugares = max(0, evento.vagas - len(evento.inscricoes)) if evento.vagas else None
    return EventDetailOut(
        id=evento.id,
        titulo=evento.titulo,
        slug=evento.slug,
        resumo=evento.resumo,
        descricao=evento.descricao,
        imagem_url=evento.imagem_url,
        local=evento.local,
        cidade=evento.cidade,
        inicio=evento.inicio,
        fim=evento.fim,
        formato=evento.formato,
        vagas=evento.vagas,
        inscricoes_abertas=evento.inscricoes_abertas,
        requer_inscricao=evento.requer_inscricao,
        estado=evento.estado,
        categoria_nome=evento.categoria.nome if evento.categoria else None,
        lugares_disponiveis=lugares,
    )


@router.put("/eventos/{event_id}", response_model=EventDetailOut)
def actualizar_evento(
    event_id: int,
    payload: EventUpdate,
    current_user: User = Depends(require_permissions(PERM_EVENTOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> EventDetailOut:
    evento = db.get(Event, event_id)
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado."
        )
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(evento, campo, valor)
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_EVENTO,
        user_id=current_user.id,
        entity="event",
        entity_id=evento.id,
        request=request,
    )
    db.commit()
    db.refresh(evento)
    return _evento_out(evento)


@router.delete("/eventos/{event_id}", response_model=MessageOut)
def cancelar_evento(
    event_id: int,
    current_user: User = Depends(require_permissions(PERM_EVENTOS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> MessageOut:
    evento = db.get(Event, event_id)
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado."
        )
    evento.estado = EventStatus.CANCELADO
    evento.inscricoes_abertas = False
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_EVENTO,
        user_id=current_user.id,
        entity="event",
        entity_id=evento.id,
        detalhe="Cancelamento de evento.",
        request=request,
    )
    db.commit()
    return MessageOut(mensagem="Evento cancelado.")


@router.get("/eventos/{event_id}/inscricoes")
def listar_inscricoes_evento(
    event_id: int,
    current_user: User = Depends(require_permissions(PERM_EVENTOS_GERIR)),
    db: Session = Depends(get_db),
) -> list[dict]:
    inscricoes = (
        db.query(EventRegistration)
        .filter(EventRegistration.event_id == event_id)
        .order_by(EventRegistration.created_at.desc())
        .all()
    )
    return [
        {
            "id": i.id,
            "nome": i.nome,
            "email": i.email,
            "telefone": i.telefone,
            "estado": i.estado,
            "criado_em": i.created_at,
        }
        for i in inscricoes
    ]


# ---------------------------------------------------------------------------
# Campanhas e publicidade
# ---------------------------------------------------------------------------
@router.get("/campanhas", response_model=list[CampaignAdminOut])
def listar_campanhas_admin(
    current_user: User = Depends(require_permissions(PERM_CAMPANHAS_GERIR)),
    db: Session = Depends(get_db),
) -> list[CampaignAdminOut]:
    campanhas = db.query(Campaign).order_by(Campaign.created_at.desc()).all()
    return [CampaignAdminOut.model_validate(c) for c in campanhas]


@router.post("/campanhas", response_model=CampaignAdminOut, status_code=status.HTTP_201_CREATED)
def criar_campanha(
    payload: CampaignCreate,
    current_user: User = Depends(require_permissions(PERM_CAMPANHAS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> CampaignAdminOut:
    dados = payload.model_dump()
    slug = dados.pop("slug", None) or _slug_unico(db, Campaign, dados["nome"])
    campanha = Campaign(slug=slug, **dados)
    db.add(campanha)
    db.flush()
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_CAMPANHA,
        user_id=current_user.id,
        entity="campaign",
        entity_id=campanha.id,
        detalhe=f"Criação da campanha «{campanha.nome}».",
        request=request,
    )
    db.commit()
    db.refresh(campanha)
    return CampaignAdminOut.model_validate(campanha)


@router.put("/campanhas/{campaign_id}", response_model=CampaignAdminOut)
def actualizar_campanha(
    campaign_id: int,
    payload: CampaignUpdate,
    current_user: User = Depends(require_permissions(PERM_CAMPANHAS_GERIR)),
    db: Session = Depends(get_db),
    request: Request = None,
) -> CampaignAdminOut:
    campanha = db.get(Campaign, campaign_id)
    if campanha is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campanha não encontrada."
        )
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(campanha, campo, valor)
    log_audit(
        db,
        action=AuditAction.ATUALIZAR_CAMPANHA,
        user_id=current_user.id,
        entity="campaign",
        entity_id=campanha.id,
        request=request,
    )
    db.commit()
    db.refresh(campanha)
    return CampaignAdminOut.model_validate(campanha)


@router.get("/anuncios", response_model=list[AdvertisementOut])
def listar_anuncios(
    current_user: User = Depends(require_permissions(PERM_CAMPANHAS_GERIR)),
    db: Session = Depends(get_db),
) -> list[AdvertisementOut]:
    anuncios = db.query(Advertisement).order_by(Advertisement.created_at.desc()).all()
    return [AdvertisementOut.model_validate(a) for a in anuncios]


@router.post("/anuncios", response_model=AdvertisementOut, status_code=status.HTTP_201_CREATED)
def criar_anuncio(
    payload: AdvertisementCreate,
    current_user: User = Depends(require_permissions(PERM_CAMPANHAS_GERIR)),
    db: Session = Depends(get_db),
) -> AdvertisementOut:
    anuncio = Advertisement(**payload.model_dump())
    db.add(anuncio)
    db.commit()
    db.refresh(anuncio)
    return AdvertisementOut.model_validate(anuncio)


@router.delete("/anuncios/{ad_id}", response_model=MessageOut)
def desactivar_anuncio(
    ad_id: int,
    current_user: User = Depends(require_permissions(PERM_CAMPANHAS_GERIR)),
    db: Session = Depends(get_db),
) -> MessageOut:
    anuncio = db.get(Advertisement, ad_id)
    if anuncio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Anúncio não encontrado."
        )
    anuncio.ativo = False
    db.commit()
    return MessageOut(mensagem="Anúncio desactivado.")


# ---------------------------------------------------------------------------
# Projectos e iniciativas
# ---------------------------------------------------------------------------
@router.get("/projectos", response_model=list[ProjectOut])
def listar_projectos_admin(
    current_user: User = Depends(require_permissions(PERM_EDITORIAL_GERIR)),
    db: Session = Depends(get_db),
) -> list[ProjectOut]:
    projectos = db.query(Project).order_by(Project.nome).all()
    return [ProjectOut.model_validate(p) for p in projectos]


@router.post("/projectos", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def criar_projecto(
    payload: ProjectCreate,
    current_user: User = Depends(require_permissions(PERM_EDITORIAL_GERIR)),
    db: Session = Depends(get_db),
) -> ProjectOut:
    dados = payload.model_dump()
    slug = dados.pop("slug", None) or _slug_unico(db, Project, dados["nome"])
    projecto = Project(slug=slug, **dados)
    db.add(projecto)
    db.commit()
    db.refresh(projecto)
    return ProjectOut.model_validate(projecto)


@router.put("/projectos/{project_id}", response_model=ProjectOut)
def actualizar_projecto(
    project_id: int,
    payload: ProjectUpdate,
    current_user: User = Depends(require_permissions(PERM_EDITORIAL_GERIR)),
    db: Session = Depends(get_db),
) -> ProjectOut:
    projecto = db.get(Project, project_id)
    if projecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Projecto não encontrado."
        )
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(projecto, campo, valor)
    db.commit()
    db.refresh(projecto)
    return ProjectOut.model_validate(projecto)
