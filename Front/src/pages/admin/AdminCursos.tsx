import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, GraduationCap, Search } from 'lucide-react'
import { adminApi } from '../../lib/api'
import { PageHeader } from '../../components/PageHeader'
import { EmptyState } from '../../components/EmptyState'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { estadoLabel, estadoTone } from '../../lib/labels'

type CursoAdmin = {
  id: number
  nome: string
  modalidade?: string | null
  estado?: string | null
  duracao_horas?: number | null
  categoria_nome?: string | null
}

type Filtro = 'todos' | 'publicados' | 'rascunhos' | 'arquivados'

const FILTROS: Array<{ id: Filtro; label: string }> = [
  { id: 'todos', label: 'Todos' },
  { id: 'publicados', label: 'Publicados' },
  { id: 'rascunhos', label: 'Rascunhos' },
  { id: 'arquivados', label: 'Arquivados' },
]

export default function AdminCursos() {
  const [cursos, setCursos] = useState<CursoAdmin[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)
  const [filtro, setFiltro] = useState<Filtro>('todos')
  const [busca, setBusca] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    adminApi
      .getCursos()
      .then((data) => {
        if (active) setCursos(data as CursoAdmin[])
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar os cursos.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadKey])

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLowerCase()
    return cursos.filter((curso) => {
      const estado = (curso.estado ?? '').toUpperCase()
      const correspondeFiltro =
        filtro === 'todos' ||
        (filtro === 'publicados' && estado === 'PUBLICADO') ||
        (filtro === 'rascunhos' && estado === 'RASCUNHO') ||
        (filtro === 'arquivados' && estado === 'ARQUIVADO')
      const correspondeBusca = !termo || curso.nome.toLowerCase().includes(termo)
      return correspondeFiltro && correspondeBusca
    })
  }, [cursos, filtro, busca])

  const contagem = (id: Filtro) => {
    if (id === 'todos') return cursos.length
    const alvo = id === 'publicados' ? 'PUBLICADO' : id === 'rascunhos' ? 'RASCUNHO' : 'ARQUIVADO'
    return cursos.filter((curso) => (curso.estado ?? '').toUpperCase() === alvo).length
  }

  return (
    <>
      <PageHeader
        eyebrow="Administração"
        title="Gestão de cursos"
        description="Consulte o catálogo formativo, o estado de publicação e a estrutura de cada curso."
        actions={
          <a className="btn btn--ghost btn--sm" href="#/admin/dashboard">
            Painel de gestão
          </a>
        }
      />

      {loading && <LoadingState label="A carregar cursos…" />}
      {!loading && error && <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />}

      {!loading && !error && cursos.length === 0 && (
        <EmptyState
          icon={GraduationCap}
          title="Nenhum curso registado"
          description="Os cursos criados na plataforma aparecerão nesta listagem."
        />
      )}

      {!loading && !error && cursos.length > 0 && (
        <section className="app-card app-card--flush">
          <div className="toolbar">
            <div className="toolbar__filters" role="group" aria-label="Filtrar cursos">
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

          {filtrados.length === 0 ? (
            <p className="app-card__empty app-card__empty--padded">
              Nenhum curso corresponde aos filtros selecionados.
            </p>
          ) : (
            <div className="table-scroll">
              <table className="app-table">
                <thead>
                  <tr>
                    <th scope="col">Curso</th>
                    <th scope="col">Modalidade</th>
                    <th scope="col">Duração</th>
                    <th scope="col">Estado</th>
                    <th scope="col" className="app-table__actions-col">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filtrados.map((curso) => (
                    <tr key={curso.id}>
                      <td>
                        <div className="table-course">
                          <span className="table-course__mark" aria-hidden="true">
                            {curso.nome.charAt(0)}
                          </span>
                          <span>
                            <strong>{curso.nome}</strong>
                            <small>{curso.categoria_nome || 'Sem categoria'}</small>
                          </span>
                        </div>
                      </td>
                      <td className="app-table__muted">{curso.modalidade || '—'}</td>
                      <td className="app-table__muted">
                        {curso.duracao_horas != null ? `${curso.duracao_horas}h` : '—'}
                      </td>
                      <td>
                        <span className={`badge badge--${estadoTone(curso.estado)}`}>
                          {estadoLabel(curso.estado)}
                        </span>
                      </td>
                      <td>
                        <div className="table-actions">
                          <a
                            className="btn btn--outline btn--sm"
                            href={`#/cursos/${curso.id}`}
                          >
                            Ver conteúdo
                            <ArrowRight size={14} aria-hidden="true" />
                          </a>
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
