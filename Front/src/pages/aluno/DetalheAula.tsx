import { useEffect, useState } from 'react'
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  Download,
  FileText,
  Radio,
  RotateCcw,
  Video,
} from 'lucide-react'
import { alunoApi, type DetalheAula as DetalheAulaData } from '../../lib/api'
import { PageHeader } from '../../components/PageHeader'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'

export default function DetalheAula({ courseId, lessonId }: { courseId: number; lessonId: number }) {
  const [aula, setAula] = useState<DetalheAulaData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    alunoApi
      .getDetalheAula(courseId, lessonId)
      .then((data) => {
        if (active) setAula(data)
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar a aula.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [courseId, lessonId, reloadKey])

  if (loading) return <LoadingState label="A carregar a aula…" />
  if (error) return <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />
  if (!aula) return null

  const marcarConcluida = async () => {
    if (saving) return
    setSaving(true)
    const novoEstado = !aula.concluida

    try {
      await alunoApi.postProgresso(courseId, {
        lesson_id: lessonId,
        concluida: novoEstado,
        percentagem_video: novoEstado ? 100 : 0,
      })
      setAula((prev) =>
        prev
          ? {
              ...prev,
              concluida: novoEstado,
              percentagem_video: novoEstado ? 100 : 0,
            }
          : prev,
      )
    } catch {
      window.alert('Não foi possível atualizar o progresso. Tente novamente.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <PageHeader
        eyebrow={`Aula · ${aula.tipo}`}
        title={aula.titulo}
        description={aula.descricao || undefined}
        actions={
          <a className="btn btn--ghost btn--sm" href={`#/cursos/${courseId}`}>
            <ArrowLeft size={15} aria-hidden="true" />
            Voltar ao curso
          </a>
        }
      />

      <div className="lesson-layout">
        <div className="lesson-main">
          {aula.video_url ? (
            <div className="lesson-video">
              <video controls className="lesson-video__player" poster="/brand/clop-brand-poster.jpg">
                <source src={aula.video_url} type="video/mp4" />
                O seu navegador não suporta vídeo.
              </video>
            </div>
          ) : (
            <div className="lesson-placeholder">
              <span aria-hidden="true">
                <FileText size={26} />
              </span>
              <p>Conteúdo em texto — leia com atenção e marque a aula como concluída no final.</p>
            </div>
          )}

          {aula.link_live && (
            <div className="lesson-live">
              <span className="lesson-live__icon" aria-hidden="true">
                <Radio size={18} />
              </span>
              <div>
                <strong>Aula ao vivo</strong>
                {aula.data_live && <p>{new Date(aula.data_live).toLocaleString('pt-PT')}</p>}
              </div>
              <a
                href={aula.link_live}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn--gold btn--sm"
              >
                Entrar na sessão
              </a>
            </div>
          )}

          {aula.conteudo && (
            <article
              className="lesson-content"
              dangerouslySetInnerHTML={{ __html: aula.conteudo }}
            />
          )}

          {aula.materiais.length > 0 && (
            <section className="app-card materials">
              <div className="app-card__header">
                <h3>Materiais de apoio</h3>
                <span className="app-card__count">{aula.materiais.length}</span>
              </div>
              <ul className="materials__list">
                {aula.materiais.map((material) => (
                  <li key={material.id}>
                    <a
                      href={material.url ?? '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="material-link"
                      aria-disabled={!material.url}
                    >
                      <span className="material-link__icon" aria-hidden="true">
                        <FileText size={16} />
                      </span>
                      <span className="material-link__body">
                        <strong>{material.titulo}</strong>
                        <small>
                          {material.tipo}
                          {material.descricao ? ` · ${material.descricao}` : ''}
                        </small>
                      </span>
                      <Download size={16} aria-hidden="true" />
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

        <aside className="lesson-aside">
          <section className="app-card">
            <div className="app-card__header">
              <h3>Progresso da aula</h3>
            </div>

            <div className={`lesson-status${aula.concluida ? ' is-done' : ''}`}>
              <span className="lesson-status__icon" aria-hidden="true">
                <CheckCircle2 size={20} />
              </span>
              <div>
                <strong>{aula.concluida ? 'Aula concluída' : 'Aula pendente'}</strong>
                <small>{aula.percentagem_video}% do conteúdo visualizado</small>
              </div>
            </div>

            <div className="progress">
              <div className="progress__track">
                <div
                  className="progress__fill"
                  style={{ width: `${Math.min(aula.percentagem_video, 100)}%` }}
                />
              </div>
            </div>

            <button
              type="button"
              className={`btn btn--block ${aula.concluida ? 'btn--outline' : 'btn--gold'}`}
              onClick={marcarConcluida}
              disabled={saving}
            >
              {aula.concluida ? (
                <>
                  <RotateCcw size={15} aria-hidden="true" />
                  Marcar como pendente
                </>
              ) : (
                <>
                  <CheckCircle2 size={15} aria-hidden="true" />
                  Marcar como concluída
                </>
              )}
            </button>
          </section>

          <section className="app-card">
            <div className="app-card__header">
              <h3>Detalhes</h3>
            </div>
            <dl className="summary-list">
              <div className="summary-list__row">
                <dt>
                  <Video size={15} aria-hidden="true" /> Tipo
                </dt>
                <dd>{aula.tipo}</dd>
              </div>
              <div className="summary-list__row">
                <dt>
                  <Clock size={15} aria-hidden="true" /> Duração
                </dt>
                <dd>{aula.duracao_minutos} min</dd>
              </div>
              <div className="summary-list__row">
                <dt>
                  <CheckCircle2 size={15} aria-hidden="true" /> Obrigatória
                </dt>
                <dd>{aula.obrigatoria ? 'Sim' : 'Não'}</dd>
              </div>
            </dl>
          </section>
        </aside>
      </div>
    </>
  )
}
