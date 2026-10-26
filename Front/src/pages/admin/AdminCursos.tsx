import { useEffect, useState } from 'react'
import { adminApi } from '../../lib/api'

export default function AdminCursos() {
  const [cursos, setCursos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    adminApi.getCursos()
      .then((data) => { if (active) setCursos(data) })
      .catch(() => { if (active) setError('Não foi possível carregar os cursos.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  if (loading) return <div className="clop-loader">A carregar…</div>
  if (error) return <div className="clop-erro">{error}</div>

  return (
    <div className="clop-pagina">
      <header className="clop-pagina__cabecalho">
        <h1>Gestão de Cursos</h1>
        <a href="#/admin/dashboard" className="clop-btn clop-btn--ghost">← Dashboard admin</a>
      </header>

      {cursos.length === 0 ? (
        <div className="clop-vazio">
          <p>Nenhum curso encontrado.</p>
        </div>
      ) : (
        <div className="clop-tabela">
          <table>
            <thead>
              <tr><th>Curso</th><th>Modalidade</th><th>Estado</th><th>Ações</th></tr>
            </thead>
            <tbody>
              {cursos.map((c: any) => (
                <tr key={c.id} className="clop-linha-curso">
                  <td><strong>{c.nome}</strong></td>
                  <td>{c.modalidade}</td>
                  <td><span className={`clop-badge clop-badge--${c.estado.toLowerCase()}`}>{c.estado}</span></td>
                  <td>
                    <a href={`#/cursos/${c.id}`} className="clop-btn clop-btn--outline clop-btn--small">Ver conteúdo</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}