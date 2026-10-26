import { useEffect, useState } from 'react'
import { authApi } from '../../lib/api'

export default function Perfil() {
  const [perfil, setPerfil] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    authApi.me()
      .then((res) => { if (active) setPerfil(res) })
      .catch(() => { if (active) setError('Não foi possível carregar o perfil.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  if (loading) return <div className="clop-loader">A carregar…</div>
  if (error) return <div className="clop-erro">{error}</div>
  if (!perfil) return null

  return (
    <div className="clop-pagina">
      <header className="clop-pagina__cabecalho">
        <h1>Perfil</h1>
        <a href="#/dashboard" className="clop-btn clop-btn--ghost">← Dashboard</a>
      </header>

      <div className="clop-perfil-card">
        <div className="clop-perfil__avatar">
          {perfil.nome_completo?.charAt(0) || perfil.email?.charAt(0)}
        </div>
        <div className="clop-perfil__dados">
          <h2>{perfil.nome_completo}</h2>
          <p className="clop-perfil__email">{perfil.email}</p>
          <p className="clop-perfil__funcao">{perfil.role || 'Aluno'}</p>
          {perfil.telefone && <p>Telefone: {perfil.telefone}</p>}
          {perfil.provincia && <p>Província: {perfil.provincia}</p>}
        </div>
        <div className="clop-perfil__acoes">
          <button className="clop-btn clop-btn--primary" onClick={() => {
            authApi.logout()
            window.location.hash = '#/entrar'
          }}>Sair da conta</button>
        </div>
      </div>
    </div>
  )
}