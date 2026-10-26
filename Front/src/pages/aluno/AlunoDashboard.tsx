import { useEffect, useState } from 'react'
import { alunoApi, type DashboardAluno, type InscricaoAluno } from '../../lib/api'
import { useAuth } from '../../contexts/AuthContext'

export default function AlunoDashboard({ user }: { user: any }) {
  const { refreshUser } = useAuth()
  const [dashboard, setDashboard] = useState<DashboardAluno | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    alunoApi.getDashboard()
      .then((data) => { if (active) setDashboard(data) })
      .catch(() => { if (active) setError('Não foi possível carregar o dashboard.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [reloadKey])

  if (loading) return <div className="clop-loader">A carregar…</div>
  if (error) return <div className="clop-erro">{error}</div>

  const m = dashboard?.metricas

  return (
    <div className="clop-dashboard">
      <header className="clop-dashboard__header">
        <div className="clop-dashboard__boas-vindas">
          <h1>Área do Aluno</h1>
          <p>Bem-vindo(a), {user.nome_completo || user.email}</p>
        </div>
        <div className="clop-dashboard__acoes">
          <a href="#/perfil" className="clop-btn clop-btn--outline">Perfil</a>
          <button
            className="clop-btn clop-btn--ghost"
            onClick={() => {
              setReloadKey((key) => key + 1)
              void refreshUser()
            }}
          >
            Atualizar
          </button>
        </div>
      </header>

      <section className="clop-dashboard__metricas">
        <div className="clop-metrica">
          <div className="clop-metrica__valor">{m?.total_inscricoes ?? 0}</div>
          <div className="clop-metrica__titulo">Total de inscrições</div>
          <div className="clop-metrica__subtotal">{m?.inscricoes_ativas ?? 0} ativas</div>
        </div>
        <div className="clop-metrica">
          <div className="clop-metrica__valor">{m?.progresso_medio ?? 0}%</div>
          <div className="clop-metrica__titulo">Progresso médio</div>
          <div className="clop-metrica__subtotal">{m?.inscricoes_concluidas ?? 0} concluídas</div>
        </div>
        <div className="clop-metrica clop-metrica--alarme">
          <div className="clop-metrica__valor">{dashboard?.notificacoes_nao_lidas ?? 0}</div>
          <div className="clop-metrica__titulo">Notificações não lidas</div>
        </div>
        <div className="clop-metrica">
          <div className="clop-metrica__valor">{m?.proximos_eventos ?? 0}</div>
          <div className="clop-metrica__titulo">Eventos próximos</div>
        </div>
      </section>

      <section className="clop-dashboard__cursos">
        <div className="clop-section-header">
          <h2>Minhas inscrições</h2>
          <a href="#/inscricoes" className="clop-link">Ver todas →</a>
        </div>
        {dashboard?.cursos?.length === 0 ? (
          <div className="clop-vazio">
            <p>Nenhuma inscrição encontrada.</p>
            <a href="#" className="clop-btn clop-btn--primary">Explorar cursos</a>
          </div>
        ) : (
          <div className="clop-lista-cursos">
            {dashboard?.cursos?.map((inscricao) => (
              <CardInscricao key={inscricao.id} inscricao={inscricao} />
            ))}
          </div>
        )}
      </section>

      <section className="clop-dashboard__proximas-aulas">
        <div className="clop-section-header"><h2>Próximas aulas</h2></div>
        {dashboard?.proximas_aulas?.length === 0 ? (
          <p className="clop-texto-vazio">Nenhuma aula pendente no momento.</p>
        ) : (
          <ul className="clop-lista-aulas">
            {dashboard?.proximas_aulas?.map((aula) => (
              <li key={aula.aula_id} className="clop-item-aula">
                <div className="clop-item-aula__info">
                  <strong>{aula.curso_nome}</strong><span>{aula.aula_titulo}</span>
                </div>
                <div className="clop-item-aula__meta">
                  <span>{aula.duracao_minutos} min</span><span>{aula.tipo}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

function CardInscricao({ inscricao }: { inscricao: InscricaoAluno }) {
  const progresso = inscricao.percentagem_progresso
  const concluida = inscricao.estado === 'CONCLUIDA'

  return (
    <article className={`clop-card-inscricao ${concluida ? 'concluida' : ''}`}>
      <div className="clop-card-inscricao__imagem">
        {inscricao.curso_imagem ? (
          <img src={inscricao.curso_imagem} alt="" />
        ) : (
          <div className="clop-card-inscricao__placeholder">{inscricao.curso_nome.charAt(0)}</div>
        )}
      </div>
      <div className="clop-card-inscricao__conteudo">
        <div className="clop-card-inscricao__cabecalho">
          <h3>{inscricao.curso_nome}</h3>
          <span className={`clop-badge clop-badge--${inscricao.estado.toLowerCase()}`}>
            {inscricao.estado}
          </span>
        </div>
        <p className="clop-card-inscricao__modalidade">
          {inscricao.curso_modalidade} · {inscricao.curso_duracao_horas}h
        </p>
        <div className="clop-card-inscricao__progresso">
          <div className="clop-progresso__label">
            <span>Progresso</span>
            <span>{progresso}%</span>
          </div>
          <div className="clop-progresso__barra">
            <div className="clop-progresso__enchimento" style={{ width: `${Math.min(progresso, 100)}%` }} />
          </div>
        </div>
        <div className="clop-card-inscricao__acoes">
          {concluida && inscricao.certificado_disponivel ? (
            <a href="#/certificados" className="clop-btn clop-btn--primary clop-btn--small">Certificado</a>
          ) : (
            <a href={`#/cursos/${inscricao.course_id}`} className="clop-btn clop-btn--outline clop-btn--small">Continuar</a>
          )}
        </div>
      </div>
    </article>
  )
}