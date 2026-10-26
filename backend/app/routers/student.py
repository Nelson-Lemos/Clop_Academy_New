from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import CurrentUser
from app.models.catalog import (
    Course,
    Enrollment,
    EnrollmentStatus,
    Lesson,
    ProgressRecord,
)
from app.models.enrollment import (
    Assessment,
    Payment,
    PaymentStatus,
    Submission,
)
from app.models.messaging import AuditAction, Notification
from app.schemas.common import MessageOut, NotificationOut
from app.schemas.enrollment import (
    CertificateOut,
    EnrollmentCourseOut,
    EnrollmentCreate,
    EnrollmentOut,
    EnrollmentStateUpdate,
    PaymentOut,
    ProgressUpdate,
    SubmissionCreate,
    SubmissionOut,
)
from app.services import assessment_service, enrollment_service
from app.services.audit_service import log_audit
from app.services.certificate_service import emitir_certificado
from app.services.dashboard_service import dashboard_aluno
from app.services.notification_service import notify

router = APIRouter(prefix="/aluno", tags=["área do aluno"])


def _agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _obter_inscricao(db: Session, user_id: int, course_id: int) -> Enrollment:
    inscricao = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        .first()
    )
    if inscricao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Não estás inscrito neste curso.",
        )
    return inscricao


def _inscricao_out(db: Session, inscricao: Enrollment) -> EnrollmentCourseOut:
    curso = inscricao.curso
    aulas = enrollment_service.aulas_do_curso(curso)
    concluidas = (
        db.query(ProgressRecord)
        .filter(
            ProgressRecord.enrollment_id == inscricao.id,
            ProgressRecord.concludida.is_(True),
        )
        .count()
    )

    registos = {
        r.lesson_id: r
        for r in db.query(ProgressRecord)
        .filter(ProgressRecord.enrollment_id == inscricao.id)
        .all()
    }
    proxima = None
    proxima_id = None
    for aula in aulas:
        registo = registos.get(aula.id)
        if registo is None or not registo.concludida:
            proxima = aula.titulo
            proxima_id = aula.id
            break

    return EnrollmentCourseOut(
        **{
            "id": inscricao.id,
            "course_id": inscricao.course_id,
            "cohort_id": inscricao.cohort_id,
            "estado": inscricao.estado,
            "preco_pago": inscricao.preco_pago,
            "termos_aceites": inscricao.termos_aceites,
            "percentagem_progresso": inscricao.percentagem_progresso,
            "iniciado_em": inscricao.iniciado_em,
            "concluido_em": inscricao.concluido_em,
            "criado_em": inscricao.created_at,
        },
        curso_nome=curso.nome,
        curso_slug=curso.slug,
        curso_imagem=curso.imagem_url,
        curso_modalidade=curso.modalidade,
        curso_duracao_horas=curso.duracao_horas,
        total_aulas=len(aulas),
        aulas_concluidas=concluidas,
        proxima_aula=proxima,
        proxima_aula_id=proxima_id,
        avaliacoes_pendentes=enrollment_service.avaliacoes_pendentes(db, inscricao),
        certificado_disponivel=(
            inscricao.estado == EnrollmentStatus.CONCLUIDA
        ),
    )


# ---------------------------------------------------------------------------
# Dashboard e inscrições
# ---------------------------------------------------------------------------
@router.get("/dashboard")
def dashboard(current_user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    inscricoes = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == current_user.id)
        .order_by(Enrollment.updated_at.desc())
        .all()
    )
    metricas = dashboard_aluno(db, current_user.id)

    nao_lidas = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.lida.is_(False),
        )
        .count()
    )

    proximas_aulas: list[dict] = []
    for inscricao in inscricoes:
        if inscricao.estado != EnrollmentStatus.ACTIVA:
            continue
        curso = inscricao.curso
        aulas = enrollment_service.aulas_do_curso(curso)
        registos = {
            r.lesson_id: r
            for r in db.query(ProgressRecord)
            .filter(ProgressRecord.enrollment_id == inscricao.id).all()
        }
        for aula in aulas:
            registo = registos.get(aula.id)
            if registo is None or not registo.concludida:
                proximas_aulas.append(
                    {
                        "curso_id": curso.id,
                        "curso_nome": curso.nome,
                        "aula_id": aula.id,
                        "aula_titulo": aula.titulo,
                        "duracao_minutos": aula.duracao_minutos,
                        "tipo": aula.tipo,
                    }
                )
                break

    return {
        "metricas": metricas,
        "notificacoes_nao_lidas": nao_lidas,
        "cursos": [_inscricao_out(db, i) for i in inscricoes],
        "proximas_aulas": proximas_aulas[:5],
    }


@router.get("/inscricoes", response_model=list[EnrollmentCourseOut])
def listar_inscricoes(
    current_user: CurrentUser, db: Session = Depends(get_db)
) -> list[EnrollmentCourseOut]:
    inscricoes = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == current_user.id)
        .order_by(Enrollment.updated_at.desc())
        .all()
    )
    return [_inscricao_out(db, i) for i in inscricoes]


@router.post("/inscricoes", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def inscrever(
    payload: EnrollmentCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    request: Request = None,
) -> EnrollmentOut:
    """Cria a inscrição de um aluno num curso.

    A prevenção de inscrições duplicadas e a validação do preço são
    garantidas no servidor.
    """
    curso = db.get(Course, payload.course_id)
    if curso is None or curso.estado != "PUBLISHED":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Curso não encontrado."
        )

    permitido, motivo = enrollment_service.curso_pode_inscrever(curso)
    if not permitido:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=motivo)

    if not payload.aceite_termos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="É necessário aceitar os termos do curso para concluir a inscrição.",
        )

    existente = enrollment_service.inscricao_existente(
        db, current_user.id, curso.id
    )
    if existente is not None and existente.estado != EnrollmentStatus.CANCELADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já estás inscrito neste curso.",
        )

    if curso.vagas_maximas:
        total = enrollment_service.contar_inscricoes(db, curso.id)
        if total >= curso.vagas_maximas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este curso não tem vagas disponíveis.",
            )

    if existente is not None:
        inscricao = existente
        inscricao.estado = EnrollmentStatus.PENDENTE
        inscricao.termos_aceites = True
        inscricao.preco_pago = curso.preco
    else:
        inscricao = Enrollment(
            user_id=current_user.id,
            course_id=curso.id,
            cohort_id=payload.cohort_id,
            estado=EnrollmentStatus.PENDENTE,
            termos_aceites=True,
            preco_pago=curso.preco,
        )
        db.add(inscricao)
        db.flush()

    pagamento = enrollment_service.criar_pagamento(
        db, inscricao=inscricao, user=current_user, metodo="MANUAL"
    )

    if curso.preco and curso.preco > 0:
        inscricao.estado = EnrollmentStatus.AGUARDA_PAGAMENTO
    else:
        inscricao.estado = EnrollmentStatus.ACTIVA
        inscricao.iniciado_em = _agora()
        pagamento.estado = PaymentStatus.CONFIRMADO
        pagamento.confirmado_em = _agora()
        pagamento.confirmado_por = current_user.id
        pagamento.notas = "Curso gratuito — inscrição activada automaticamente."

    notify(
        db,
        user_id=current_user.id,
        titulo="Inscrição registada",
        mensagem=(
            f"A tua inscrição em «{curso.nome}» foi registada. "
            + (
                "O acesso será activado após a confirmação do pagamento."
                if inscricao.estado == EnrollmentStatus.AGUARDA_PAGAMENTO
                else "Já tens acesso ao conteúdo do curso."
            )
        ),
        tipo="INSCRICAO",
        ligacao=f"/aluno/cursos/{curso.id}",
    )
    log_audit(
        db,
        action=AuditAction.CRIAR_INSCRICAO,
        user_id=current_user.id,
        entity="enrollment",
        entity_id=inscricao.id,
        detalhe=(
            f"Inscrição em «{curso.nome}» (referência de pagamento "
            f"{pagamento.referencia})."
        ),
        request=request,
    )
    db.commit()
    db.refresh(inscricao)
    return EnrollmentOut.model_validate(inscricao)


@router.post("/inscricoes/{inscricao_id}/cancelar", response_model=MessageOut)
def cancelar_inscricao(
    inscricao_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    request: Request = None,
) -> MessageOut:
    inscricao = db.get(Enrollment, inscricao_id)
    if inscricao is None or inscricao.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada."
        )
    if inscricao.estado == EnrollmentStatus.CONCLUIDA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível cancelar uma inscrição concluída.",
        )

    inscricao.estado = EnrollmentStatus.CANCELADA
    log_audit(
        db,
        action=AuditAction.CANCELAR_INSCRICAO,
        user_id=current_user.id,
        entity="enrollment",
        entity_id=inscricao.id,
        request=request,
    )
    db.commit()
    return MessageOut(
        mensagem="Inscrição cancelada.",
        detalhe="Podes voltar a inscrever-te enquanto as inscrições estiverem abertas.",
    )


# ---------------------------------------------------------------------------
# Sala de aulas
# ---------------------------------------------------------------------------
@router.get("/cursos/{course_id}/conteudo")
def conteudo_curso(
    course_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
) -> dict:
    """Estrutura do curso com o progresso do aluno. Exige inscrição válida."""
    inscricao = _obter_inscricao(db, current_user.id, course_id)
    if not enrollment_service.aluno_tem_acesso(inscricao):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "O acesso ao conteúdo ainda não está activo. "
                "Confirma o pagamento da inscrição."
            ),
        )

    curso = inscricao.curso
    registos = {
        r.lesson_id: r
        for r in db.query(ProgressRecord)
        .filter(ProgressRecord.enrollment_id == inscricao.id)
        .all()
    }

    modulos = []
    for modulo in curso.modulos:
        aulas = []
        for aula in modulo.aulas:
            registo = registos.get(aula.id)
            aulas.append(
                {
                    "id": aula.id,
                    "titulo": aula.titulo,
                    "descricao": aula.descricao,
                    "tipo": aula.tipo,
                    "ordem": aula.ordem,
                    "duracao_minutos": aula.duracao_minutos,
                    "video_url": aula.video_url,
                    "link_live": aula.link_live,
                    "data_live": aula.data_live,
                    "obrigatoria": aula.obrigatoria,
                    "conteudo": aula.conteudo,
                    "materiais": [
                        {
                            "id": m.id,
                            "titulo": m.titulo,
                            "descricao": m.descricao,
                            "tipo": m.tipo,
                            "url": m.url,
                        }
                        for m in aula.materiais
                    ],
                    "concluida": bool(registo and registo.concludida),
                    "percentagem_video": registo.percentagem_video if registo else 0,
                    "ultima_posicao_segundos": (
                        registo.ultima_posicao_segundos if registo else 0
                    ),
                }
            )
        modulos.append(
            {
                "id": modulo.id,
                "titulo": modulo.titulo,
                "descricao": modulo.descricao,
                "ordem": modulo.ordem,
                "aulas": aulas,
            }
        )

    return {
        "curso": {
            "id": curso.id,
            "nome": curso.nome,
            "slug": curso.slug,
            "modalidade": curso.modalidade,
            "duracao_horas": curso.duracao_horas,
            "percentagem_conclusao_minima": curso.percentagem_conclusao_minima,
        },
        "inscricao": {
            "id": inscricao.id,
            "estado": inscricao.estado,
            "percentagem_progresso": inscricao.percentagem_progresso,
            "iniciado_em": inscricao.iniciado_em,
            "concluido_em": inscricao.concluido_em,
        },
        "modulos": modulos,
    }


@router.get("/cursos/{course_id}/aulas/{lesson_id}")
def detalhe_aula(
    course_id: int,
    lesson_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict:
    inscricao = _obter_inscricao(db, current_user.id, course_id)
    if not enrollment_service.aluno_tem_acesso(inscricao):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O acesso a este conteúdo ainda não está activo.",
        )

    aula = db.get(Lesson, lesson_id)
    if aula is None or aula.modulo is None or aula.modulo.curso_id != course_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Aula não encontrada."
        )

    registo = (
        db.query(ProgressRecord)
        .filter(
            ProgressRecord.enrollment_id == inscricao.id,
            ProgressRecord.lesson_id == lesson_id,
        )
        .first()
    )

    return {
        "id": aula.id,
        "titulo": aula.titulo,
        "descricao": aula.descricao,
        "tipo": aula.tipo,
        "duracao_minutos": aula.duracao_minutos,
        "conteudo": aula.conteudo,
        "video_url": aula.video_url,
        "link_live": aula.link_live,
        "data_live": aula.data_live,
        "obrigatoria": aula.obrigatoria,
        "materiais": [
            {
                "id": m.id,
                "titulo": m.titulo,
                "descricao": m.descricao,
                "tipo": m.tipo,
                "url": m.url,
            }
            for m in aula.materiais
        ],
        "concluida": bool(registo and registo.concludida),
        "percentagem_video": registo.percentagem_video if registo else 0,
        "ultima_posicao_segundos": registo.ultima_posicao_segundos if registo else 0,
    }


@router.post("/cursos/{course_id}/progresso")
def actualizar_progresso(
    course_id: int,
    payload: ProgressUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict:
    inscricao = _obter_inscricao(db, current_user.id, course_id)
    if not enrollment_service.aluno_tem_acesso(inscricao):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O acesso a este conteúdo ainda não está activo.",
        )

    try:
        enrollment_service.marcar_aula_concluida(
            db,
            inscricao,
            payload.lesson_id,
            percentagem_video=payload.percentagem_video,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    db.commit()
    return {
        "percentagem_progresso": inscricao.percentagem_progresso,
        "estado_inscricao": inscricao.estado,
    }


# ---------------------------------------------------------------------------
# Avaliações
# ---------------------------------------------------------------------------
@router.get("/avaliacoes")
def listar_avaliacoes(
    current_user: CurrentUser, db: Session = Depends(get_db)
) -> list[dict]:
    inscricoes = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.estado.in_(
                [EnrollmentStatus.ACTIVA, EnrollmentStatus.CONCLUIDA]
            ),
        )
        .all()
    )
    course_ids = {i.course_id for i in inscricoes}
    if not course_ids:
        return []

    avaliacoes = (
        db.query(Assessment)
        .filter(
            Assessment.course_id.in_(course_ids),
            Assessment.published.is_(True),
        )
        .order_by(Assessment.id)
        .all()
    )

    resultado = []
    for avaliacao in avaliacoes:
        submissoes = (
            db.query(Submission)
            .filter(
                Submission.assessment_id == avaliacao.id,
                Submission.user_id == current_user.id,
            )
            .order_by(Submission.tentativa.desc())
            .all()
        )
        ultima = submissoes[0] if submissoes else None
        resultado.append(
            {
                "id": avaliacao.id,
                "course_id": avaliacao.course_id,
                "titulo": avaliacao.titulo,
                "descricao": avaliacao.descricao,
                "tipo": avaliacao.tipo,
                "nota_maxima": avaliacao.nota_maxima,
                "nota_aprovacao": avaliacao.nota_aprovacao,
                "tempo_limite_minutos": avaliacao.tempo_limite_minutos,
                "tentativas_maximas": avaliacao.tentativas_maximas,
                "disponivel_de": avaliacao.disponivel_de,
                "disponivel_ate": avaliacao.disponivel_ate,
                "total_perguntas": len(avaliacao.perguntas),
                "tentativas_usadas": len(submissoes),
                "ultima_nota": ultima.nota if ultima else None,
                "ultima_submissao": ultima.submetida_em if ultima else None,
                "corrigida": bool(ultima and ultima.estado == "CORRIGIDA"),
                "feedback": ultima.feedback if ultima else None,
            }
        )
    return resultado


@router.get("/avaliacoes/{assessment_id}")
def detalhe_avaliacao(
    assessment_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
) -> dict:
    avaliacao = db.get(Assessment, assessment_id)
    if avaliacao is None or not avaliacao.published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Avaliação não encontrada."
        )

    inscricao = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == avaliacao.course_id,
            Enrollment.estado.in_(
                [EnrollmentStatus.ACTIVA, EnrollmentStatus.CONCLUIDA]
            ),
        )
        .first()
    )
    if inscricao is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não estás inscrito no curso desta avaliação.",
        )

    submissoes = (
        db.query(Submission)
        .filter(
            Submission.assessment_id == avaliacao.id,
            Submission.user_id == current_user.id,
        )
        .order_by(Submission.tentativa.desc())
        .all()
    )
    ultima = submissoes[0] if submissoes else None

    return {
        "id": avaliacao.id,
        "course_id": avaliacao.course_id,
        "titulo": avaliacao.titulo,
        "descricao": avaliacao.descricao,
        "tipo": avaliacao.tipo,
        "nota_maxima": avaliacao.nota_maxima,
        "nota_aprovacao": avaliacao.nota_aprovacao,
        "tempo_limite_minutos": avaliacao.tempo_limite_minutos,
        "tentativas_maximas": avaliacao.tentativas_maximas,
        "tentativas_usadas": len(submissoes),
        "ultima_nota": ultima.nota if ultima else None,
        "corrigida": bool(ultima and ultima.estado == "CORRIGIDA"),
        "feedback": ultima.feedback if ultima else None,
        "perguntas": [
            {
                "id": p.id,
                "enunciado": p.enunciado,
                "tipo": p.tipo,
                "opcoes": assessment_service.opcoes_para_texto(p.opcoes),
                "pontos": p.pontos,
                "ordem": p.ordem,
            }
            for p in avaliacao.perguntas
        ],
    }


@router.post("/avaliacoes/submissao", response_model=SubmissionOut)
def submeter_avaliacao(
    payload: SubmissionCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    request: Request = None,
) -> SubmissionOut:
    avaliacao = db.get(Assessment, payload.assessment_id)
    if avaliacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Avaliação não encontrada."
        )

    inscricao = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == avaliacao.course_id,
            Enrollment.estado.in_(
                [EnrollmentStatus.ACTIVA, EnrollmentStatus.CONCLUIDA]
            ),
        )
        .first()
    )
    if inscricao is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não tens inscrição activa neste curso.",
        )

    try:
        submissao = assessment_service.submeter(
            db,
            inscricao=inscricao,
            assessment_id=payload.assessment_id,
            respostas=payload.respostas,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    log_audit(
        db,
        action=AuditAction.SUBMETER_AVALIACAO,
        user_id=current_user.id,
        entity="submission",
        entity_id=submissao.id,
        detalhe=f"Submissão de «{avaliacao.titulo}».",
        request=request,
    )
    db.commit()
    db.refresh(submissao)
    return SubmissionOut.model_validate(submissao)


@router.get("/avaliacoes/{assessment_id}/historico")
def historico_avaliacao(
    assessment_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
) -> list[SubmissionOut]:
    submissoes = (
        db.query(Submission)
        .filter(
            Submission.assessment_id == assessment_id,
            Submission.user_id == current_user.id,
        )
        .order_by(Submission.tentativa.desc())
        .all()
    )
    return [SubmissionOut.model_validate(s) for s in submissoes]


# ---------------------------------------------------------------------------
# Pagamentos do aluno
# ---------------------------------------------------------------------------
@router.get("/pagamentos", response_model=list[PaymentOut])
def listar_pagamentos(
    current_user: CurrentUser, db: Session = Depends(get_db)
) -> list[PaymentOut]:
    pagamentos = (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )
    return [PaymentOut.model_validate(p) for p in pagamentos]


# ---------------------------------------------------------------------------
# Certificados
# ---------------------------------------------------------------------------
@router.get("/certificados", response_model=list[CertificateOut])
def listar_certificados(
    current_user: CurrentUser, db: Session = Depends(get_db)
) -> list[CertificateOut]:
    from app.models.market import Certificate

    certificados = (
        db.query(Certificate)
        .filter(Certificate.user_id == current_user.id)
        .order_by(Certificate.emitido_em.desc())
        .all()
    )
    resultado = []
    for certificado in certificados:
        item = CertificateOut.model_validate(certificado)
        item.curso_nome = certificado.curso.nome if certificado.curso else None
        item.aluno_nome = current_user.nome_completo
        resultado.append(item)
    return resultado


@router.post("/certificados/{inscricao_id}/emitir", response_model=CertificateOut)
def solicitar_certificado(
    inscricao_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
) -> CertificateOut:
    """Solicita a emissão de um certificado (verificada no servidor)."""
    inscricao = db.get(Enrollment, inscricao_id)
    if inscricao is None or inscricao.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada."
        )

    try:
        certificado = emitir_certificado(db, inscricao_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    log_audit(
        db,
        action=AuditAction.EMITIR_CERTIFICADO,
        user_id=current_user.id,
        entity="certificate",
        entity_id=certificado.id,
        detalhe=f"Emissão de certificado para «{inscricao.curso.nome}».",
    )
    db.commit()
    db.refresh(certificado)

    item = CertificateOut.model_validate(certificado)
    item.curso_nome = certificado.curso.nome if certificado.curso else None
    item.aluno_nome = current_user.nome_completo
    return item


# ---------------------------------------------------------------------------
# Notificações
# ---------------------------------------------------------------------------
@router.get("/notificacoes", response_model=list[NotificationOut])
def listar_notificacoes(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    apenas_nao_lidas: bool = False,
) -> list[NotificationOut]:
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if apenas_nao_lidas:
        query = query.filter(Notification.lida.is_(False))
    return [NotificationOut.model_validate(n) for n in query.order_by(
        Notification.created_at.desc()
    ).all()]


@router.post("/notificacoes/{notification_id}/ler")
def marcar_notificacao_lida(
    notification_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
) -> dict:
    notificacao = db.get(Notification, notification_id)
    if notificacao is None or notificacao.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada."
        )
    notificacao.lida = True
    db.commit()
    return {"ok": True}


@router.post("/notificacoes/ler-todas")
def marcar_todas_lidas(
    current_user: CurrentUser, db: Session = Depends(get_db)
) -> dict:
    atualizadas = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.lida.is_(False),
        )
        .update({"lida": True}, synchronize_session=False)
    )
    db.commit()
    return {"ok": True, "actualizadas": atualizadas}


@router.post("/inscricoes/{inscricao_id}/estado")
def alterar_estado_inscricao(
    inscricao_id: int,
    payload: EnrollmentStateUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict:
    """Actualiza o estado de uma inscrição do utilizador (ex.: conclusão)."""
    inscricao = db.get(Enrollment, inscricao_id)
    if inscricao is None or inscricao.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada."
        )

    inscricao.estado = payload.estado
    db.commit()
    return {"id": inscricao.id, "estado": inscricao.estado}
