import { useEffect, useState } from 'react'
import { alunoApi } from '../../lib/api'

export default function Notificacoes() {
  const [notificacoes, setNotificacoes] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    alunoApi.getNotificacoes()
      .then((data) => { if (active) setNotificacoes(data) })
      .catch(() => { if (active) setError('Não foi possível carregar as notificações.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const marcarLida = async (id: number) => {
    try {
      await alunoApi.postMarcarNotificacaoLida(id)
      setNotificacoes((prev) => prev.map((n) => n.id === id ? { ...n, lida: true } : n))
    } catch {}
  }

  const marcarTodas = async () => {
    try {
      await alunoApi.postMarcarTodasLidas()
      setNotificacoes((prev) => prev.map((n) => ({ ...n, lida: true })))
    } catch {}
  }

  if (loading) return <div className="clop-loader">A carregar…</div>
  if (error) return <div className="clop-erro">{error}</div>

  return (
    <div className="clop-pagina">
      <header className="clop-pagina__cabecalho">
        <h1>Notificações</h1>
        <div className="clop-pagina__acoes">
          <button className="clop-btn clop-btn--ghost" onClick={marcarTodas}>Marcar todas como lidas</button>
          <a href="#/dashboard" className="clop-btn clop-btn--ghost">← Dashboard</a>
        </div>
      </header>

      {notificacoes.length === 0 ? (
        <div className="clop-vazio">
          <p>Nenhuma notificação encontrada.</p>
        </div>
      ) : (
        <div className="clop-lista-notificacoes">
          {notificacoes.map((n) => (
            <div key={n.id} className={`clop-item-notificacao ${!n.lida ? 'nao-lida' : ''}`}>
              <div className="clop-item-notificacao__conteudo">
                <strong>{n.titulo}</strong>
                <p>{n.mensagem}</p>
                <span className="clop-data-notificacao">{new Date(n.criado_em).toLocaleString()}</span>
              </div>
              {!n.lida && (
                <button className="clop-btn clop-btn--ghost clop-btn--small" onClick={() => marcarLida(n.id)}>
                  Marcar como lida
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}