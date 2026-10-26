import { useEffect, useState } from 'react'
import { alunoApi } from '../../lib/api'

export default function Avaliacoes() {
  const [avaliacoes, setAvaliacoes] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    alunoApi.getAvaliacoes()
      .then((data) => { if (active) setAvaliacoes(data) })
      .catch(() => { if (active) setError('Não foi possível carregar as avaliações.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  if (loading) return <div className="clop-loader">A carregar…</div>
  if (error) return <div className="clop-erro">{error}</div>

  return (
    <div className="clop-pagina">
      <header className="clop-pagina__cabecalho">
        <h1>Avaliações</h1>
        <a href="#/dashboard" className="clop-btn clop-btn--ghost">← Dashboard</a>
      </header>

      {avaliacoes.length === 0 ? (
        <div className="clop-vazio">
          <p>Nenhuma avaliação disponível no momento.</p>
        </div>
      ) : (
        <div className="clop-lista-avaliacoes">
          {avaliacoes.map((a) => (
            <div key={a.id} className="clop-card-avaliacao">
              <div className="clop-card-avaliacao__cabecalho">
                <h3>{a.titulo}</h3>
                <span className={`clop-badge clop-badge--${a.corrigida ? 'ok' : 'pendente'}`}>
                  {a.corrigida ? 'Corrigida' : 'Pendente'}
                </span>
              </div>
              {a.descricao && <p className="clop-card-avaliacao__descricao">{a.descricao}</p>}
              <div className="clop-card-avaliacao__meta">
                <span>{a.total_perguntas} perguntas</span>
                <span>{a.tentativas_usadas} / {a.tentativas_maximas} tentativas</span>
                <span>Nota mínima: {a.nota_aprovacao}</span>
                {a.ultima_nota !== null && <span>Última nota: {a.ultima_nota}</span>}
              </div>
              <div className="clop-card-avaliacao__acoes">
                <a href={`#/avaliacoes/${a.id}`} className="clop-btn clop-btn--primary">
                  {a.corrigida ? 'Ver resultado' : 'Fazer avaliação'}
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}