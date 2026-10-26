import { useEffect, useState } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  BookOpenCheck,
  Clock,
  FileText,
  GraduationCap,
  PlayCircle,
  Radio,
  Video,
} from 'lucide-react'
import { alunoApi, type AulaCurso, type ConteudoCurso as ConteudoCursoData } from '../../lib/api'
import { PageHeader } from '../../components/PageHeader'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { estadoLabel, estadoTone } from '../../lib/labels'

export default function ConteudoCurso({ courseId }: { courseId: number }) {
  const [conteudo, setConteudo] = useState<ConteudoCursoData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    alunoApi
      .getConteudoCurso(courseId)
      .then((data) => {
        if (active) setConteudo(data)
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar o conteúdo do curso.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [courseId, reloadKey])

  if (loading) return <LoadingState label="A carregar o curso…" />
  if (error) return <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />
  if (!conteudo) return null

  const { curso, inscricao, modulos } = conteudo
  const totalAulas = modulos.reduce((total, modulo) => total + modulo.aulas.length, 0)
  const aulasConcluidas = modulos.reduce(
    (total, modulo) => total + modulo.aulas.filter((aula) => aula.concluida).length,
    0,
  )
  const proximaAula = modulos.flatMap((modulo) => modulo.aulas).find((aula) => !aula.concluida)
  const progresso = Math.min(inscricao.percentagem_progresso, 100)

  return (
    <>
      <PageHeader
        eyebrow="Sala de aula"
        title={curso.nome}
        description={`${inscricao.percentagem_progresso}% concluído · ${aulasConcluidas} de ${totalAulas} aulas`}
        actions={
          <a className="btn btn--ghost btn--sm" href="#/inscricoes">
            <ArrowLeft size={15} aria-hidden="true" />
            Os meus cursos
          </a>
        }
      />

      <div className="course-layout">
        <section className="curriculum" aria-label="Conteúdo programático">
          {modulos.length === 0 ? (
            <div className="app-card">
              <p className="app-card__empty">Este curso ainda não tem módulos publicados.</p>
            </div>
          ) : (
            modulos.map((modulo, index) => {
              const concluidasModulo = modulo.aulas.filter((aula) => aula.concluida).length
              const completo = modulo.aulas.length > 0 && concluidasModulo === modulo.aulas.length

              return (
                <details key={modulo.id} className="module" open={index === 0}>
                  <summary className="module__summary">
                    <span className={`module__marker${completo ? ' is-complete' : ''}`} aria-hidden="true">
                      {completo ? <BookOpenCheck size={16} /> : index + 1}
                    </span>
                    <span className="module__heading">
                      <strong>{modulo.titulo}</strong>
                      <small>
                        {concluidasModulo} / {modulo.aulas.length} aulas concluídas
                      </small>
                    </span>
                    <span className="module__chevron" aria-hidden="true" />
                  </summary>

                  {modulo.descricao && <p className="module__desc">{modulo.descricao}</p>}

                  <ul className="module__lessons">
                    {modulo.aulas.map((aula) => (
                      <li key={aula.id}>
                        <a
                          href={`#/aulas/${courseId}/${aula.id}`}
                          className={`lesson-row${aula.concluida ? ' is-done' : ''}`}
                        >
                          <span className="lesson-row__status" aria-hidden="true">
                            {aula.concluida ? <BookOpenCheck size={16} /> : <AulaIcon tipo={aula.tipo} />}
                          </span>
                          <span className="lesson-row__body">
                            <strong>{aula.titulo}</strong>
                            <small>
                              {aula.tipo} · {aula.duracao_minutos} min
                              {aula.obrigatoria ? ' · obrigatória' : ''}
                            </small>
                          </span>
                          <span className="lesson-row__meta">
                            {aula.concluida ? (
                              <span className="lesson-row__done">Concluída</span>
                            ) : (
                              <ArrowRight size={15} aria-hidden="true" />
                            )}
                          </span>
                        </a>
                      </li>
                    ))}
                  </ul>
                </details>
              )
            })
          )}
        </section>

        <aside className="course-aside">
          <section className="app-card course-summary">
            <div className="course-summary__head">
              <span className="course-summary__badge">
                <GraduationCap size={16} aria-hidden="true" />
                Resumo do curso
              </span>
              <span className={`badge badge--${estadoTone(inscricao.estado)}`}>
                {estadoLabel(inscricao.estado)}
              </span>
            </div>

            <div className="course-summary__progress">
              <div className="progress">
                <div className="progress__label">
                  <span>Progresso</span>
                  <strong>{inscricao.percentagem_progresso}%</strong>
                </div>
                <div className="progress__track">
                  <div className="progress__fill" style={{ width: `${progresso}%` }} />
                </div>
              </div>
              <p className="course-summary__lessons">
                {aulasConcluidas} de {totalAulas} aulas concluídas
              </p>
            </div>

            <dl className="summary-list">
              <div className="summary-list__row">
                <dt>
                  <Clock size={15} aria-hidden="true" /> Duração
                </dt>
                <dd>{curso.duracao_horas}h</dd>
              </div>
              <div className="summary-list__row">
                <dt>
                  <Video size={15} aria-hidden="true" /> Modalidade
                </dt>
                <dd>{curso.modalidade}</dd>
              </div>
              <div className="summary-list__row">
                <dt>
                  <BookOpenCheck size={15} aria-hidden="true" /> Módulos
                </dt>
                <dd>{modulos.length}</dd>
              </div>
              <div className="summary-list__row">
                <dt>
                  <GraduationCap size={15} aria-hidden="true" /> Conclusão mínima
                </dt>
                <dd>{curso.percentagem_conclusao_minima}%</dd>
              </div>
            </dl>

            {proximaAula ? (
              <a className="btn btn--gold btn--block" href={`#/aulas/${courseId}/${proximaAula.id}`}>
                <PlayCircle size={16} aria-hidden="true" />
                Continuar aprendizagem
              </a>
            ) : (
              <a className="btn btn--gold btn--block" href="#/certificados">
                <BookOpenCheck size={16} aria-hidden="true" />
                Ver certificados
              </a>
            )}
          </section>
        </aside>
      </div>
    </>
  )
}

function AulaIcon({ tipo }: { tipo: AulaCurso['tipo'] }) {
  const normalized = (tipo || '').toUpperCase()
  if (normalized.includes('VIDEO')) return <Video size={16} />
  if (normalized.includes('LIVE')) return <Radio size={16} />
  if (normalized.includes('TEXTO') || normalized.includes('LEITURA')) return <FileText size={16} />
  return <PlayCircle size={16} />
}
