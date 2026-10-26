import { useEffect, useState } from 'react'
import { alunoApi } from '../../lib/api'

export default function Certificados({ user }: { user: any }) {
  const [certificados, setCertificados] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    alunoApi.getCertificados()
      .then((data) => { if (active) setCertificados(data) })
      .catch(() => { if (active) setError('Não foi possível carregar os certificados.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  if (loading) return <div className="clop-loader">A carregar…</div>
  if (error) return <div className="clop-erro">{error}</div>

  return (
    <div className="clop-pagina">
      <header className="clop-pagina__cabecalho">
        <h1>Meus Certificados</h1>
        <a href="#/dashboard" className="clop-btn clop-btn--ghost">← Dashboard</a>
      </header>

      {certificados.length === 0 ? (
        <div className="clop-vazio">
          <p>Nenhum certificado emitido ainda.</p>
          <p className="clop-destaque-secundario">Conclua um curso para receber o seu certificado.</p>
        </div>
      ) : (
        <div className="clop-lista-certificados">
          {certificados.map((c) => (
            <div key={c.id} className="clop-card-certificado">
              <div className="clop-card-certificado__cabecalho">
                <h3>{c.curso_nome}</h3>
                <span className={`clop-badge clop-badge--${c.estado.toLowerCase()}`}>{c.estado}</span>
              </div>
              <div className="clop-card-certificado__codigo">
                <strong>Código:</strong> {c.codigo}
              </div>
              <div className="clop-card-certificado__detalhes">
                <span>Aluno: {c.aluno_nome}</span>
                <span>Emitido em: {new Date(c.emitido_em).toLocaleDateString()}</span>
                {c.nota_final !== null && <span>Nota final: {c.nota_final}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}