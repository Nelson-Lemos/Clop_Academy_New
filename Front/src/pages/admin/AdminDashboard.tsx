import { useEffect, useState } from 'react'
import {
  ArrowRight,
  Award,
  BookOpen,
  CalendarDays,
  CreditCard,
  FileText,
  GraduationCap,
  LayoutGrid,
  Mail,
  Users,
} from 'lucide-react'
import { adminApi, type AuthUser, type DashboardAdmin } from '../../lib/api'
import { PageHeader } from '../../components/PageHeader'
import { StatCard } from '../../components/StatCard'
import { ErrorState } from '../../components/ErrorState'
import { DashboardSkeleton } from '../../components/LoadingState'
import { EmptyState } from '../../components/EmptyState'
import { firstName, greeting, todayLabel } from '../../lib/labels'

export default function AdminDashboard({ user }: { user: AuthUser }) {
  const [metricas, setMetricas] = useState<DashboardAdmin | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    adminApi
      .getDashboard()
      .then((data) => {
        if (active) setMetricas(data)
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar o painel de gestão.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadKey])

  const recarregar = () => setReloadKey((key) => key + 1)
  const totalInscricoesCurso = metricas?.inscricoes_por_curso.reduce((total, curso) => total + curso.total, 0) ?? 0
  const maiorCurso = Math.max(1, ...(metricas?.inscricoes_por_curso.map((curso) => curso.total) ?? [0]))

  return (
    <>
      <PageHeader
        eyebrow={todayLabel()}
        title={`${greeting()}, ${firstName(user.nome_completo) || 'administrador'}`}
        description="Visão consolidada da atividade da plataforma, inscrições e operação diária."
        actions={
          <button type="button" className="btn btn--ghost btn--sm" onClick={recarregar}>
            Atualizar dados
          </button>
        }
      />

      {loading && <DashboardSkeleton />}
      {!loading && error && <ErrorState message={error} onRetry={recarregar} />}

      {!loading && !error && metricas && (
        <>
          <section className="stat-grid" aria-label="Indicadores administrativos">
            <StatCard
              icon={Users}
              label="Alunos registados"
              value={metricas.alunos_registados}
              hint="contas ativas na plataforma"
              tone="gold"
            />
            <StatCard
              icon={BookOpen}
              label="Inscrições ativas"
              value={metricas.inscricoes_activas}
              hint={`${metricas.total_inscricoes} no total`}
              tone="green"
            />
            <StatCard
              icon={GraduationCap}
              label="Cursos publicados"
              value={metricas.cursos_publicados}
              hint={`${metricas.cursos_activos} ativos`}
              tone="blue"
            />
            <StatCard
              icon={CreditCard}
              label="Pagamentos pendentes"
              value={metricas.pagamentos_pendentes}
              hint={`${metricas.pagamentos_confirmados} confirmados`}
              tone={metricas.pagamentos_pendentes > 0 ? 'red' : 'neutral'}
            />
            <StatCard
              icon={Award}
              label="Certificados emitidos"
              value={metricas.certificados_emitidos}
              hint="concluídos com certificação"
              tone="gold"
            />
            <StatCard
              icon={CalendarDays}
              label="Eventos publicados"
              value={metricas.eventos_publicados}
              hint={`${metricas.eventos_proximos} próximos`}
              tone="blue"
            />
          </section>

          <div className="dashboard-grid dashboard-grid--admin">
            <section className="app-card dashboard-grid__main">
              <div className="app-card__header app-card__header--stack">
                <div>
                  <h3>Inscrições por curso</h3>
                  <p className="app-card__subtitle">
                    {totalInscricoesCurso} inscrição(ões) distribuídas pelo catálogo
                  </p>
                </div>
                <a className="app-link app-link--sm" href="#/admin/cursos">
                  Gerir cursos
                  <ArrowRight size={14} aria-hidden="true" />
                </a>
              </div>

              {metricas.inscricoes_por_curso.length === 0 ? (
                <EmptyState
                  icon={LayoutGrid}
                  title="Sem inscrições registadas"
                  description="Quando os alunos se inscreverem nos cursos, a distribuição aparecerá aqui."
                />
              ) : (
                <div className="bar-chart" role="list" aria-label="Inscrições por curso">
                  {metricas.inscricoes_por_curso.map((curso) => {
                    const percentagem = Math.round((curso.total / maiorCurso) * 100)
                    return (
                      <div key={curso.curso_id} className="bar-chart__row" role="listitem">
                        <span className="bar-chart__label" title={curso.curso}>
                          {curso.curso}
                        </span>
                        <span className="bar-chart__track">
                          <span className="bar-chart__fill" style={{ width: `${percentagem}%` }} />
                        </span>
                        <span className="bar-chart__value">{curso.total}</span>
                      </div>
                    )
                  })}
                </div>
              )}
            </section>

            <aside className="dashboard-aside">
              <section className="app-card">
                <div className="app-card__header">
                  <h3>Resumo operacional</h3>
                </div>
                <ul className="ops-list">
                  <OpsRow icon={FileText} label="Artigos publicados" value={metricas.artigos_publicados} />
                  <OpsRow icon={Mail} label="Pedidos de contacto" value={metricas.pedidos_contacto} />
                  <OpsRow icon={CreditCard} label="Pagamentos confirmados" value={metricas.pagamentos_confirmados} />
                  <OpsRow icon={BookOpen} label="Avaliações pendentes" value={metricas.avaliacoes_pendentes} />
                </ul>
              </section>

              <section className="app-card">
                <div className="app-card__header">
                  <h3>Ações rápidas</h3>
                </div>
                <div className="quick-links">
                  <a className="quick-link" href="#/admin/cursos">
                    <span className="quick-link__icon" aria-hidden="true">
                      <GraduationCap size={17} />
                    </span>
                    <span>
                      <strong>Gestão de cursos</strong>
                      <small>Catálogo, módulos e aulas</small>
                    </span>
                    <ArrowRight size={15} aria-hidden="true" />
                  </a>
                  <a className="quick-link" href="#inicio">
                    <span className="quick-link__icon" aria-hidden="true">
                      <LayoutGrid size={17} />
                    </span>
                    <span>
                      <strong>Portal institucional</strong>
                      <small>Ver o site público</small>
                    </span>
                    <ArrowRight size={15} aria-hidden="true" />
                  </a>
                  <a className="quick-link" href="#/perfil">
                    <span className="quick-link__icon" aria-hidden="true">
                      <Users size={17} />
                    </span>
                    <span>
                      <strong>O meu perfil</strong>
                      <small>Dados da conta</small>
                    </span>
                    <ArrowRight size={15} aria-hidden="true" />
                  </a>
                </div>
              </section>
            </aside>
          </div>
        </>
      )}
    </>
  )
}

function OpsRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof FileText
  label: string
  value: number
}) {
  return (
    <li className="ops-list__row">
      <span className="ops-list__icon" aria-hidden="true">
        <Icon size={16} />
      </span>
      <span>{label}</span>
      <strong>{value}</strong>
    </li>
  )
}
