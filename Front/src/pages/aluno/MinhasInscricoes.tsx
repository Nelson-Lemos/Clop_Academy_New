import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, BookOpen, Search } from 'lucide-react'
import { alunoApi, type InscricaoAluno } from '../../lib/api'
import { PageHeader } from '../../components/PageHeader'
import { EmptyState } from '../../components/EmptyState'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { estadoLabel, estadoTone } from '../../lib/labels'

type Filtro = 'todas' | 'andamento' | 'concluidas' | 'pendentes'

const FILTROS: Array<{ id: Filtro; label: string }> = [
  { id: 'todas', label: 'Todas' },
  { id: 'andamento', label: 'Em andamento' },
  { id: 'concluidas', label: 'Concluídas' },
  { id: 'pendentes', label: 'Pendentes' },
]

export default function MinhasInscricoes() {
  const [inscricoes, setInscricoes] = useState<InscricaoAluno[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)
  const [filtro, setFiltro] = useState<Filtro>('todas')
  const [busca, setBusca] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    alunoApi
      .getInscricoes()
      .then((data) => {
        if (active) setInscricoes(data)
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar as inscrições.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadKey])

  const filtradas = useMemo(() => {
    const termo = busca.trim().toLowerCase()
    return inscricoes.filter((inscricao) => {
      const estado = inscricao.estado.toUpperCase()
      const correspondeFiltro =
        filtro === 'todas' ||
        (filtro === 'concluidas' && estado === 'CONCLUIDA') ||
        (filtro === 'pendentes' && ['PENDENTE', 'AGUARDA_PAGAMENTO', 'CANCELADA'].includes(estado)) ||
        (filtro === 'andamento' && !['CONCLUIDA', 'PENDENTE', 'AGUARDA_PAGAMENTO', 'CANCELADA'].includes(estado))
      const correspondeBusca =
        !termo ||
        inscricao.curso_nome.toLowerCase().includes(termo) ||
        inscricao.curso_modalidade.toLowerCase().includes(termo)
      return correspondeFiltro && correspondeBusca
    })
  }, [inscricoes, filtro, busca])

  const contagem = (id: Filtro) => {
    if (id === 'todas') return inscricoes.length
    if (id === 'concluidas') return inscricoes.filter((i) => i.estado.toUpperCase() === 'CONCLUIDA').length
    if (id === 'pendentes')
      return inscricoes.filter((i) => ['PENDENTE', 'AGUARDA_PAGAMENTO', 'CANCELADA'].includes(i.estado.toUpperCase())).length
    return inscricoes.filter(
      (i) => !['CONCLUIDA', 'PENDENTE', 'AGUARDA_PAGAMENTO', 'CANCELADA'].includes(i.estado.toUpperCase()),
    ).length
  }

  return (
    <>
      <PageHeader
        eyebrow="Aprendizagem"
        title="Meus cursos"
        description="Consulte o estado das suas inscrições, o progresso e retome o estudo a qualquer momento."
        actions={
          <a className="btn btn--gold btn--sm" href="#formacao">
            Explorar formação
            <ArrowRight size={15} aria-hidden="true" />
          </a>
        }
      />

      {loading && <LoadingState label="A carregar inscrições…" />}
      {!loading && error && <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />}

      {!loading && !error && inscricoes.length === 0 && (
        <EmptyState
          icon={BookOpen}
          title="Ainda não tem inscrições"
          description="Consulte a oferta formativa da CLOP Academia Digital e inscreva-se no seu primeiro curso."
          action={
            <a className="btn btn--gold btn--sm" href="#formacao">
              Ver formação disponível
            </a>
          }
        />
      )}

      {!loading && !error && inscricoes.length > 0 && (
        <section className="app-card app-card--flush">
          <div className="toolbar">
            <div className="toolbar__filters" role="group" aria-label="Filtrar inscrições">
              {FILTROS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`filter-chip${filtro === item.id ? ' is-active' : ''}`}
                  aria-pressed={filtro === item.id}
                  onClick={() => setFiltro(item.id)}
                >
                  {item.label}
                  <span className="filter-chip__count">{contagem(item.id)}</span>
                </button>
              ))}
            </div>
            <label className="toolbar__search">
              <Search size={16} aria-hidden="true" />
              <input
                type="search"
                placeholder="Pesquisar curso…"
                value={busca}
                onChange={(event) => setBusca(event.target.value)}
                aria-label="Pesquisar curso"
              />
            </label>
          </div>

          {filtradas.length === 0 ? (
            <p className="app-card__empty app-card__empty--padded">Nenhum curso corresponde aos filtros selecionados.</p>
          ) : (
            <div className="table-scroll">
              <table className="app-table">
                <thead>
                  <tr>
                    <th scope="col">Curso</th>
                    <th scope="col">Estado</th>
                    <th scope="col">Progresso</th>
                    <th scope="col">Aulas</th>
                    <th scope="col">Próxima aula</th>
                    <th scope="col" className="app-table__actions-col">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {filtradas.map((inscricao) => (
                    <tr key={inscricao.id}>
                      <td>
                        <div className="table-course">
                          <span className="table-course__mark" aria-hidden="true">
                            {inscricao.curso_nome.charAt(0)}
                          </span>
                          <span>
                            <strong>{inscricao.curso_nome}</strong>
                            <small>
                              {inscricao.curso_modalidade} · {inscricao.curso_duracao_horas}h
                            </small>
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge badge--${estadoTone(inscricao.estado)}`}>
                          {estadoLabel(inscricao.estado)}
                        </span>
                      </td>
                      <td>
                        <div className="progress progress--compact">
                          <div className="progress__label">
                            <strong>{inscricao.percentagem_progresso}%</strong>
                          </div>
                          <div className="progress__track">
                            <div
                              className="progress__fill"
                              style={{ width: `${Math.min(inscricao.percentagem_progresso, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="app-table__muted">
                        {inscricao.aulas_concluidas} / {inscricao.total_aulas}
                      </td>
                      <td className="app-table__muted">{inscricao.proxima_aula || '—'}</td>
                      <td>
                        <div className="table-actions">
                          <a
                            className="btn btn--outline btn--sm"
                            href={`#/cursos/${inscricao.course_id}`}
                          >
                            {inscricao.estado.toUpperCase() === 'CONCLUIDA' ? 'Rever' : 'Acessar'}
                          </a>
                          {inscricao.certificado_disponivel && (
                            <a className="btn btn--ghost btn--sm" href="#/certificados">
                              Certificado
                            </a>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </>
  )
}
