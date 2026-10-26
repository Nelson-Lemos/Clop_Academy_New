import { useEffect, useState, type CSSProperties } from 'react'
import {
  ArrowRight,
  Award,
  Bell,
  BookOpen,
  CalendarClock,
  Clock,
  PlayCircle,
  TrendingUp,
} from 'lucide-react'
import {
  alunoApi,
  type AuthUser,
  type DashboardAluno,
  type InscricaoAluno,
  type NotificacaoAluno,
} from '../../lib/api'
import { useAuth } from '../../contexts/AuthContext'
import { PageHeader } from '../../components/PageHeader'
import { StatCard } from '../../components/StatCard'
import { EmptyState } from '../../components/EmptyState'
import { ErrorState } from '../../components/ErrorState'
import { DashboardSkeleton } from '../../components/LoadingState'
import {
  estadoLabel,
  estadoTone,
  firstName,
  greeting,
  todayLabel,
} from '../../lib/labels'

export default function AlunoDashboard({ user }: { user: AuthUser }) {
  const { refreshUser } = useAuth()
  const [dashboard, setDashboard] = useState<DashboardAluno | null>(null)
  const [notificacoes, setNotificacoes] = useState<NotificacaoAluno[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    Promise.all([
      alunoApi.getDashboard(),
      alunoApi.getNotificacoes().catch(() => [] as NotificacaoAluno[]),
    ])
      .then(([dashboardData, notificacoesData]) => {
        if (!active) return
        setDashboard(dashboardData)
        setNotificacoes(notificacoesData.slice(0, 4))
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar o dashboard.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadKey])

  const recarregar = () => {
    setReloadKey((key) => key + 1)
    void refreshUser()
  }

  const metricas = dashboard?.metricas
  const cursos = dashboard?.cursos ?? []
  const emAndamento = cursos.filter((curso) => curso.estado.toUpperCase() !== 'CONCLUIDA')
  const continuar = emAndamento[0] ?? cursos[0]
  const naoLidas = dashboard?.notificacoes_nao_lidas ?? 0

  return (
    <>
      <PageHeader
        eyebrow={todayLabel()}
        title={`${greeting()}, ${firstName(user.nome_completo) || 'aluno'}`}
        description="Acompanhe o seu progresso, retome os cursos e mantenha-se a par das novidades da CLOP."
        actions={
          <button type="button" className="btn btn--ghost btn--sm" onClick={recarregar}>
            Atualizar dados
          </button>
        }
      />

      {loading && <DashboardSkeleton />}

      {!loading && error && <ErrorState message={error} onRetry={recarregar} />}

      {!loading && !error && dashboard && (
        <>
          <section className="student-hero">
            <span className="student-hero__glow" aria-hidden="true" />
            <div className="student-hero__content">
              <p className="student-hero__eyebrow">
                <span aria-hidden="true" />
                {continuar ? 'A sua aprendizagem' : 'Comece hoje'}
              </p>
              <h2>{continuar ? 'Retome de onde parou' : 'Construa o seu futuro financeiro'}</h2>
              <p>
                {continuar
                  ? `Continue a aprender em “${continuar.curso_nome}”. Cada aula concluída aproxima-o do certificado.`
                  : 'Explore a formação da CLOP Academia Digital e inscreva-se no seu primeiro curso.'}
              </p>
              <div className="student-hero__actions">
                {continuar ? (
                  <a className="btn btn--gold" href={`#/cursos/${continuar.course_id}`}>
                    Continuar curso
                    <ArrowRight size={16} aria-hidden="true" />
                  </a>
                ) : (
                  <a className="btn btn--gold" href="#formacao">
                    Explorar formação
                    <ArrowRight size={16} aria-hidden="true" />
                  </a>
                )}
                <a className="btn btn--ghost-light" href="#/inscricoes">
                  Os meus cursos
                </a>
              </div>
            </div>

            {continuar && (
              <div className="student-hero__progress">
                <div
                  className="progress-ring"
                  style={{ '--ring-value': `${Math.min(continuar.percentagem_progresso, 100) * 3.6}deg` } as CSSProperties}
                  role="img"
                  aria-label={`Progresso de ${continuar.percentagem_progresso}%`}
                >
                  <span>{continuar.percentagem_progresso}%</span>
                </div>
                <p className="student-hero__course">{continuar.curso_nome}</p>
                <small>
                  {continuar.aulas_concluidas} de {continuar.total_aulas} aulas concluídas
                </small>
              </div>
            )}
          </section>

          <section className="stat-grid" aria-label="Indicadores de aprendizagem">
            <StatCard
              icon={BookOpen}
              label="Inscrições ativas"
              value={metricas?.inscricoes_ativas ?? 0}
              hint={`${metricas?.total_inscricoes ?? 0} no total`}
              tone="gold"
            />
            <StatCard
              icon={TrendingUp}
              label="Progresso médio"
              value={`${metricas?.progresso_medio ?? 0}%`}
              hint={`${metricas?.inscricoes_concluidas ?? 0} curso(s) concluído(s)`}
              tone="green"
            />
            <StatCard
              icon={Bell}
              label="Notificações"
              value={naoLidas}
              hint={naoLidas === 1 ? '1 por ler' : 'por ler'}
              tone={naoLidas > 0 ? 'red' : 'neutral'}
            />
            <StatCard
              icon={CalendarClock}
              label="Eventos próximos"
              value={metricas?.proximos_eventos ?? 0}
              hint="na agenda CLOP"
              tone="blue"
            />
          </section>

          <div className="dashboard-grid">
            <section className="app-section dashboard-grid__main">
              <div className="app-section__header">
                <div>
                  <h2>Os meus cursos</h2>
                  <p>Continue a aprendizagem a partir do ponto onde parou.</p>
                </div>
                <a className="app-link" href="#/inscricoes">
                  Ver todos
                  <ArrowRight size={15} aria-hidden="true" />
                </a>
              </div>

              {cursos.length === 0 ? (
                <EmptyState
                  icon={BookOpen}
                  title="Ainda não tem inscrições"
                  description="Consulte a formação disponível no portal institucional e inscreva-se no primeiro curso."
                  action={
                    <a className="btn btn--gold btn--sm" href="#formacao">
                      Explorar formação
                    </a>
                  }
                />
              ) : (
                <div className="course-grid">
                  {cursos.slice(0, 4).map((inscricao) => (
                    <CursoCard key={inscricao.id} inscricao={inscricao} />
                  ))}
                </div>
              )}
            </section>

            <aside className="dashboard-aside">
              <section className="app-card">
                <div className="app-card__header">
                  <h3>Próximas aulas</h3>
                  <span className="app-card__count">
                    {dashboard.proximas_aulas.length}
                  </span>
                </div>
                {dashboard.proximas_aulas.length === 0 ? (
                  <p className="app-card__empty">Nenhuma aula pendente no momento.</p>
                ) : (
                  <ul className="lesson-list">
                    {dashboard.proximas_aulas.slice(0, 4).map((aula) => (
                      <li key={aula.aula_id} className="lesson-list__item">
                        <span className="lesson-list__icon" aria-hidden="true">
                          <PlayCircle size={16} />
                        </span>
                        <div className="lesson-list__body">
                          <strong>{aula.aula_titulo}</strong>
                          <span>{aula.curso_nome}</span>
                        </div>
                        <span className="lesson-list__time">
                          <Clock size={13} aria-hidden="true" />
                          {aula.duracao_minutos} min
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              <section className="app-card">
                <div className="app-card__header">
                  <h3>Notificações</h3>
                  <a className="app-link app-link--sm" href="#/notificacoes">
                    Ver todas
                  </a>
                </div>
                {notificacoes.length === 0 ? (
                  <p className="app-card__empty">Sem notificações recentes.</p>
                ) : (
                  <ul className="notif-list">
                    {notificacoes.map((notificacao) => (
                      <li key={notificacao.id} className={`notif-list__item${notificacao.lida ? '' : ' is-unread'}`}>
                        <span className="notif-list__dot" aria-hidden="true" />
                        <div className="notif-list__body">
                          <strong>{notificacao.titulo}</strong>
                          <p>{notificacao.mensagem}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </aside>
          </div>
        </>
      )}
    </>
  )
}

function CursoCard({ inscricao }: { inscricao: InscricaoAluno }) {
  const concluida = inscricao.estado.toUpperCase() === 'CONCLUIDA'
  const progresso = Math.min(inscricao.percentagem_progresso, 100)

  return (
    <article className="course-card">
      <div className="course-card__cover">
        {inscricao.curso_imagem ? (
          <img src={inscricao.curso_imagem} alt="" loading="lazy" />
        ) : (
          <span className="course-card__initial" aria-hidden="true">
            {inscricao.curso_nome.charAt(0)}
          </span>
        )}
        <span className={`badge badge--${estadoTone(inscricao.estado)}`}>
          {estadoLabel(inscricao.estado)}
        </span>
      </div>

      <div className="course-card__body">
        <h3 className="course-card__title">{inscricao.curso_nome}</h3>
        <p className="course-card__meta">
          <span>{inscricao.curso_modalidade}</span>
          <span>{inscricao.curso_duracao_horas}h</span>
          <span>
            {inscricao.aulas_concluidas}/{inscricao.total_aulas} aulas
          </span>
        </p>

        <div className="progress">
          <div className="progress__label">
            <span>Progresso</span>
            <strong>{inscricao.percentagem_progresso}%</strong>
          </div>
          <div className="progress__track">
            <div className="progress__fill" style={{ width: `${progresso}%` }} />
          </div>
        </div>

        <div className="course-card__actions">
          {concluida && inscricao.certificado_disponivel ? (
            <a className="btn btn--gold btn--sm" href="#/certificados">
              <Award size={15} aria-hidden="true" />
              Certificado
            </a>
          ) : (
            <a className="btn btn--outline btn--sm" href={`#/cursos/${inscricao.course_id}`}>
              {concluida ? 'Rever curso' : 'Continuar'}
              <ArrowRight size={15} aria-hidden="true" />
            </a>
          )}
          {inscricao.proxima_aula && (
            <span className="course-card__next" title={inscricao.proxima_aula}>
              <PlayCircle size={14} aria-hidden="true" />
              {inscricao.proxima_aula}
            </span>
          )}
        </div>
      </div>
    </article>
  )
}
