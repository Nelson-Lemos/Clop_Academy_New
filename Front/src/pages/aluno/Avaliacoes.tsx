import { useEffect, useState } from 'react'
import { ArrowRight, ClipboardList, Clock, ListChecks, Target, Trophy } from 'lucide-react'
import { alunoApi, type AvaliacaoAluno } from '../../lib/api'
import { PageHeader } from '../../components/PageHeader'
import { EmptyState } from '../../components/EmptyState'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'

export default function Avaliacoes() {
  const [avaliacoes, setAvaliacoes] = useState<AvaliacaoAluno[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    alunoApi
      .getAvaliacoes()
      .then((data) => {
        if (active) setAvaliacoes(data)
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar as avaliações.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadKey])

  return (
    <>
      <PageHeader
        eyebrow="Avaliação"
        title="Avaliações"
        description="Consulte os testes disponíveis, as tentativas realizadas e os respetivos resultados."
      />

      {loading && <LoadingState label="A carregar avaliações…" />}
      {!loading && error && <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />}

      {!loading && !error && avaliacoes.length === 0 && (
        <EmptyState
          icon={ClipboardList}
          title="Nenhuma avaliação disponível"
          description="As avaliações dos cursos em que está inscrito aparecerão aqui quando forem publicadas."
        />
      )}

      {!loading && !error && avaliacoes.length > 0 && (
        <div className="assessment-grid">
          {avaliacoes.map((avaliacao) => {
            const corrigida = avaliacao.corrigida
            const aprovado =
              avaliacao.ultima_nota !== null && avaliacao.ultima_nota >= avaliacao.nota_aprovacao

            return (
              <article key={avaliacao.id} className="assessment-card">
                <div className="assessment-card__top">
                  <span className={`assessment-card__icon${corrigida ? ' is-done' : ''}`} aria-hidden="true">
                    {corrigida ? <Trophy size={19} /> : <ClipboardList size={19} />}
                  </span>
                  <span className={`badge badge--${corrigida ? (aprovado ? 'success' : 'danger') : 'warning'}`}>
                    {corrigida ? (aprovado ? 'Aprovada' : 'Não aprovada') : 'Disponível'}
                  </span>
                </div>

                <h3 className="assessment-card__title">{avaliacao.titulo}</h3>
                {avaliacao.descricao && (
                  <p className="assessment-card__desc">{avaliacao.descricao}</p>
                )}

                <ul className="assessment-card__meta">
                  <li>
                    <ListChecks size={14} aria-hidden="true" />
                    {avaliacao.total_perguntas} perguntas
                  </li>
                  <li>
                    <Clock size={14} aria-hidden="true" />
                    {avaliacao.tempo_limite_minutos
                      ? `${avaliacao.tempo_limite_minutos} min`
                      : 'Sem limite'}
                  </li>
                  <li>
                    <Target size={14} aria-hidden="true" />
                    Mínimo {avaliacao.nota_aprovacao}
                  </li>
                </ul>

                <div className="assessment-card__footer">
                  <div className="assessment-card__attempts">
                    <span>
                      Tentativas: <strong>{avaliacao.tentativas_usadas}</strong> / {avaliacao.tentativas_maximas}
                    </span>
                    {avaliacao.ultima_nota !== null && (
                      <span className="assessment-card__score">
                        Última nota: <strong>{avaliacao.ultima_nota}</strong>
                      </span>
                    )}
                  </div>
                  <a className="btn btn--outline btn--sm" href={`#/avaliacoes/${avaliacao.id}`}>
                    {corrigida ? 'Ver resultado' : 'Iniciar avaliação'}
                    <ArrowRight size={15} aria-hidden="true" />
                  </a>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </>
  )
}
