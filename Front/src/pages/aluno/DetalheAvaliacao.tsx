import { useEffect, useState } from 'react'
import {
  ArrowLeft,
  CheckCircle2,
  ClipboardList,
  Clock,
  ListChecks,
  Target,
  XCircle,
} from 'lucide-react'
import { alunoApi, type AvaliacaoAluno } from '../../lib/api'
import { PageHeader } from '../../components/PageHeader'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'

export default function DetalheAvaliacao({ assessmentId }: { assessmentId: number }) {
  const [avaliacao, setAvaliacao] = useState<AvaliacaoAluno | null>(null)
  const [respostas, setRespostas] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submetida, setSubmetida] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    alunoApi
      .getDetalheAvaliacao(assessmentId)
      .then((data) => {
        if (active) setAvaliacao(data)
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar a avaliação.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [assessmentId, reloadKey])

  if (loading) return <LoadingState label="A carregar avaliação…" />
  if (error) return <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />
  if (!avaliacao) return null

  if (submetida) {
    const nota = avaliacao.ultima_nota
    const aprovado = nota !== null && nota >= avaliacao.nota_aprovacao

    return (
      <>
        <PageHeader
          eyebrow="Resultado"
          title={avaliacao.titulo}
          description="Consulte o resultado da sua submissão."
          actions={
            <a className="btn btn--ghost btn--sm" href="#/avaliacoes">
              <ArrowLeft size={15} aria-hidden="true" />
              Voltar às avaliações
            </a>
          }
        />

        <div className={`result-card${aprovado ? ' is-pass' : ' is-fail'}`}>
          <span className="result-card__icon" aria-hidden="true">
            {aprovado ? <CheckCircle2 size={28} /> : <XCircle size={28} />}
          </span>
          <p className="result-card__status">{aprovado ? 'Aprovado' : 'Não aprovado'}</p>

          <div className="score-ring">
            <span className="score-ring__value">{nota ?? '—'}</span>
            <span className="score-ring__label">de {avaliacao.nota_maxima}</span>
          </div>

          <p className="result-card__feedback">
            {avaliacao.feedback || 'Sem feedback adicional.'}
          </p>

          <div className="result-card__meta">
            <span>
              <Target size={14} aria-hidden="true" /> Nota mínima: {avaliacao.nota_aprovacao}
            </span>
            <span>
              <ClipboardList size={14} aria-hidden="true" /> Tentativas: {avaliacao.tentativas_usadas} /{' '}
              {avaliacao.tentativas_maximas}
            </span>
          </div>

          <a className="btn btn--gold" href="#/avaliacoes">
            Voltar às avaliações
          </a>
        </div>
      </>
    )
  }

  const perguntas = avaliacao.perguntas ?? []
  const totalPerguntas = perguntas.length
  const respondidas = perguntas.filter((pergunta) => Boolean(respostas[pergunta.id])).length
  const percentagem = totalPerguntas === 0 ? 0 : Math.round((respondidas / totalPerguntas) * 100)

  const handleResposta = (questionId: number, value: string) => {
    setRespostas((prev) => ({ ...prev, [questionId]: value }))
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (submitting) return

    setSubmitting(true)
    setError(null)

    try {
      await alunoApi.postSubmissaoAvaliacao({
        assessment_id: assessmentId,
        respostas,
      })
      const atualizada = await alunoApi.getDetalheAvaliacao(assessmentId)
      setAvaliacao(atualizada)
      setSubmetida(true)
    } catch {
      setError('Não foi possível submeter a avaliação. Tente novamente.')
      setSubmitting(false)
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Avaliação em curso"
        title={avaliacao.titulo}
        description={avaliacao.descricao || undefined}
        actions={
          <a className="btn btn--ghost btn--sm" href="#/avaliacoes">
            <ArrowLeft size={15} aria-hidden="true" />
            Sair
          </a>
        }
      />

      <div className="quiz-layout">
        <form onSubmit={handleSubmit} className="quiz">
          {perguntas.map((pergunta) => (
            <fieldset key={pergunta.id} className="question-card">
              <legend className="question-card__legend">
                <span className="question-card__number">{pergunta.ordem + 1}</span>
                <span className="question-card__text">{pergunta.enunciado}</span>
              </legend>

              {pergunta.tipo === 'OPCAO_MULTIPLA' && pergunta.opcoes ? (
                <div className="question-card__options">
                  {pergunta.opcoes.split('|').map((opcao, index) => {
                    const valor = opcao.trim()
                    const selecionada = respostas[pergunta.id] === valor
                    return (
                      <label key={`${pergunta.id}-${index}`} className={`option${selecionada ? ' is-selected' : ''}`}>
                        <input
                          type="radio"
                          name={`q_${pergunta.id}`}
                          value={valor}
                          checked={selecionada}
                          onChange={(event) => handleResposta(pergunta.id, event.target.value)}
                        />
                        <span className="option__marker" aria-hidden="true" />
                        <span>{valor}</span>
                      </label>
                    )
                  })}
                </div>
              ) : (
                <input
                  type="text"
                  className="field__input"
                  value={respostas[pergunta.id] || ''}
                  onChange={(event) => handleResposta(pergunta.id, event.target.value)}
                  placeholder="Escreva a sua resposta…"
                  aria-label={`Resposta à pergunta ${pergunta.ordem + 1}`}
                />
              )}
            </fieldset>
          ))}

          {error && <ErrorState message={error} />}

          <div className="quiz__footer">
            <p>
              {respondidas} de {totalPerguntas} perguntas respondidas
            </p>
            <button
              type="submit"
              className="btn btn--gold"
              disabled={submitting || respondidas < totalPerguntas}
            >
              {submitting ? 'A submeter…' : 'Submeter avaliação'}
            </button>
          </div>
        </form>

        <aside className="quiz-aside">
          <section className="app-card">
            <div className="app-card__header">
              <h3>Resumo</h3>
            </div>

            <div className="quiz-progress">
              <div className="progress">
                <div className="progress__label">
                  <span>Respostas</span>
                  <strong>{percentagem}%</strong>
                </div>
                <div className="progress__track">
                  <div className="progress__fill" style={{ width: `${percentagem}%` }} />
                </div>
              </div>
            </div>

            <dl className="summary-list">
              <div className="summary-list__row">
                <dt>
                  <ListChecks size={15} aria-hidden="true" /> Perguntas
                </dt>
                <dd>{totalPerguntas}</dd>
              </div>
              <div className="summary-list__row">
                <dt>
                  <Target size={15} aria-hidden="true" /> Nota mínima
                </dt>
                <dd>{avaliacao.nota_aprovacao}</dd>
              </div>
              <div className="summary-list__row">
                <dt>
                  <Clock size={15} aria-hidden="true" /> Tempo
                </dt>
                <dd>
                  {avaliacao.tempo_limite_minutos ? `${avaliacao.tempo_limite_minutos} min` : 'Sem limite'}
                </dd>
              </div>
              <div className="summary-list__row">
                <dt>
                  <ClipboardList size={15} aria-hidden="true" /> Tentativas
                </dt>
                <dd>
                  {avaliacao.tentativas_usadas} / {avaliacao.tentativas_maximas}
                </dd>
              </div>
            </dl>

            <p className="quiz-aside__note">
              Responda a todas as perguntas para submeter. A correção é feita no servidor.
            </p>
          </section>
        </aside>
      </div>
    </>
  )
}
