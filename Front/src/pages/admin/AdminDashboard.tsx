import { useEffect, useState } from 'react'
import { adminApi } from '../../lib/api'

export default function AdminDashboard({ user }: { user: any }) {
  const [metricas, setMetricas] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    adminApi.getDashboard()
      .then((data) => { if (active) setMetricas(data) })
      .catch(() => { if (active) setError('Não foi possível carregar o dashboard administrativo.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  if (loading) return <div className="clop-loader">A carregar…</div>
  if (error) return <div className="clop-erro">{error}</div>
  if (!metricas) return null

  return (
    <div className="clop-dashboard clop-dashboard--admin">
      <header className="clop-dashboard__header">
        <div className="clop-dashboard__boas-vindas">
          <h1>Painel Administrativo</h1>
          <p>Bem-vindo(a), {user.nome_completo || user.email}</p>
        </div>
        <a href="#/dashboard" className="clop-btn clop-btn--ghost">Área do aluno</a>
      </header>

      <section className="clop-dashboard__metricas">
        <div className="clop-metrica">
          <div className="clop-metrica__valor">{metricas.alunos_registados}</div>
          <div className="clop-metrica__titulo">Alunos registados</div>
        </div>
        <div className="clop-metrica">
          <div className="clop-metrica__valor">{metricas.total_inscricoes}</div>
          <div className="clop-metrica__titulo">Total de inscrições</div>
          <div className="clop-metrica__subtotal">{metricas.inscricoes_activas} activas</div>
        </div>
        <div className="clop-metrica">
          <div className="clop-metrica__valor">{metricas.cursos_publicados}</div>
          <div className="clop-metrica__titulo">Cursos publicados</div>
        </div>
        <div className="clop-metrica clop-metrica--alarme">
          <div className="clop-metrica__valor">{metricas.pagamentos_pendentes}</div>
          <div className="clop-metrica__titulo">Pagamentos pendentes</div>
        </div>
        <div className="clop-metrica">
          <div className="clop-metrica__valor">{metricas.certificados_emitidos}</div>
          <div className="clop-metrica__titulo">Certificados emitidos</div>
        </div>
        <div className="clop-metrica">
          <div className="clop-metrica__valor">{metricas.eventos_publicados}</div>
          <div className="clop-metrica__titulo">Eventos publicados</div>
        </div>
      </section>

      <section className="clop-dashboard__cursos">
        <div className="clop-section-header">
          <h2>Inscrições por curso</h2>
          <a href="#/admin/cursos" className="clop-link">Gerir cursos →</a>
        </div>
        {metricas.inscricoes_por_curso?.length === 0 ? (
          <p className="clop-texto-vazio">Nenhuma inscrição registada.</p>
        ) : (
          <div className="clop-lista-inscricoes-curso">
            {metricas.inscricoes_por_curso.map((c: any) => (
              <div key={c.curso_id} className="clop-item-inscricao-curso">
                <span>{c.curso}</span>
                <span className="clop-valor-inscricao">{c.total}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}