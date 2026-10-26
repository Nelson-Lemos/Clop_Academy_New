from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.catalog import Course, Enrollment, EnrollmentStatus
from app.schemas.catalog import (
    CourseDetailOut,
    CourseOut,
    InstructorOut,
)


def _instructor_out(curso: Course) -> InstructorOut | None:
    instructor = curso.instructor
    if instructor is None:
        return None
    perfil = instructor.perfil_formador
    return InstructorOut(
        id=instructor.id,
        nome_completo=instructor.nome_completo,
        cargo=perfil.cargo if perfil else None,
        bio=perfil.bio if perfil else None,
        foto_url=perfil.foto_url if perfil else None,
    )


def _inscricoes_count(db: Session, course_id: int) -> int:
    return (
        db.query(Enrollment)
        .filter(
            Enrollment.course_id == course_id,
            Enrollment.estado.in_(
                [
                    EnrollmentStatus.ACTIVA,
                    EnrollmentStatus.CONCLUIDA,
                    EnrollmentStatus.AGUARDA_PAGAMENTO,
                    EnrollmentStatus.PENDENTE,
                ]
            ),
        )
        .count()
    )


def to_course_out(db: Session, curso: Course) -> CourseOut:
    count = _inscricoes_count(db, curso.id)
    vagas = None
    if curso.vagas_maximas:
        vagas = max(0, curso.vagas_maximas - count)
    return CourseOut(
        **{
            "id": curso.id,
            "nome": curso.nome,
            "slug": curso.slug,
            "descricao_resumida": curso.descricao_resumida,
            "descricao": curso.descricao,
            "objetivos": curso.objetivos,
            "conteudo_programatico": curso.conteudo_programatico,
            "requisitos": curso.requisitos,
            "modalidade": curso.modalidade,
            "nivel": curso.nivel,
            "duracao_horas": curso.duracao_horas,
            "numero_aulas": curso.numero_aulas,
            "preco": curso.preco,
            "moeda": curso.moeda,
            "imagem_url": curso.imagem_url,
            "area": curso.area,
            "estado": curso.estado,
            "inscricoes_abertas": curso.inscricoes_abertas,
            "vagas_maximas": curso.vagas_maximas,
            "data_inicio": curso.data_inicio,
            "data_fim": curso.data_fim,
        },
        formador=_instructor_out(curso),
        inscricoes_count=count,
        vagas_disponiveis=vagas,
    )


def to_course_detail(db: Session, curso: Course) -> CourseDetailOut:
    base = to_course_out(db, curso)
    return CourseDetailOut(
        **base.model_dump(),
        modulos=[
            {
                "id": modulo.id,
                "titulo": modulo.titulo,
                "descricao": modulo.descricao,
                "ordem": modulo.ordem,
                "aulas": [
                    {
                        "id": aula.id,
                        "titulo": aula.titulo,
                        "descricao": aula.descricao,
                        "tipo": aula.tipo,
                        "ordem": aula.ordem,
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
                    }
                    for aula in modulo.aulas
                ],
            }
            for modulo in curso.modulos
        ],
        turmas=[
            {
                "id": turma.id,
                "nome": turma.nome,
                "data_inicio": turma.data_inicio,
                "data_fim": turma.data_fim,
                "vagas": turma.vagas,
                "estado": turma.estado,
            }
            for turma in curso.turmas
        ],
        percentagem_conclusao_minima=curso.percentagem_conclusao_minima,
        aulas_obrigatorias_minimas=curso.aulas_obrigatorias_minimas,
    )
