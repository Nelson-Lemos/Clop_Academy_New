import { useEffect, useState } from 'react'
import { alunoApi } from '../../lib/api'

export default function Pagamentos({ user }: { user: any }) {
  const [pagamentos, setPagamentos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    alunoApi.getPagamentos()
      .then((data) => { if (active) setPagamentos(data) })
      .catch(() => { if (active) setError('Não foi possível carregar os pagamentos.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  if (loading) return <div className="clop-loader">A carregar…</div>
  if (error) return <div className="clop-erro">{error}</div>

  return (
    <div className="clop-pagina">
      <header className="clop-pagina__cabecalho">
        <h1>Meus Pagamentos</h1>
        <a href="#/dashboard" className="clop-btn clop-btn--ghost">← Dashboard</a>
      </header>

      {pagamentos.length === 0 ? (
        <div className="clop-vazio">
          <p>Nenhum pagamento encontrado.</p>
        </div>
      ) : (
        <div className="clop-tabela">
          <table>
            <thead>
              <tr><th>Referência</th><th>Valor</th><th>Método</th><th>Estado</th><th>Criado em</th></tr>
            </thead>
            <tbody>
              {pagamentos.map((p) => (
                <tr key={p.id} className="clop-linha-pagamento">
                  <td><strong>{p.referencia}</strong></td>
                  <td>{p.valor} {p.moeda}</td>
                  <td>{p.metodo}</td>
                  <td><span className={`clop-badge clop-badge--${p.estado.toLowerCase()}`}>{p.estado}</span></td>
                  <td>{new Date(p.criado_em).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}