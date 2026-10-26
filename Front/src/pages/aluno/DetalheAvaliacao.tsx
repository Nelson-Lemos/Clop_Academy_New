import { useEffect, useState } from 'react'
import { alunoApi } from '../../lib/api'

export default function DetalheAvaliacao({ assessmentId, user }: { assessmentId: number; user: any }) {
  const [avaliacao, setAvaliacao] = useState<any>(null)
  const [respostas, setRespostas] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submetida, setSubmetida] = useState(false)

  useEffect(() => {
    let active = true
    alunoApi.getDetalheAvaliacao(assessmentId)
      .then((data) => { if (active) setAvaliacao(data) })
      .catch(() => { if (active) setError('Não foi possível carregar a avaliação.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [assessmentId])

  if (loading) return <div className="clop-loader">A carregar…</div>
  if (error) return <div className="clop-erro">{error}</div>
  if (!avaliacao) return null

  if (submetida && avaliacao.ultima_nota !== null) {
    return (
      <div className="clop-pagina">
        <header className="clop-pagina__cabecalho">
          <h1>Resultado da Avaliação</h1>
          <a href="#/avaliacoes" className="clop-btn clop-btn--ghost">← Voltar</a>
        </header>
        <div className="clop-resultado-avaliacao">
          <div className="clop-nota-final">
            <span className="clop-nota-valor">{avaliacao.ultima_nota}</span>
            <span className="clop-nota-label">de {avaliacao.nota_maxima}</span>
          </div>
          <p>{avaliacao.feedback || 'Sem feedback adicional.'}</p>
          <div className="clop-resultado-status">
            {avaliacao.ultima_nota >= avaliacao.nota_aprovacao ? 'Aprovado' : 'Reprovado'}
          </div>
          <a href="#/avaliacoes" className="clop-btn clop-btn--primary">Voltar às avaliações</a>
        </div>
      </div>
    )
  }

  const handleResposta = (questionId: number, value: string) => {
    setRespostas((prev) => ({ ...prev, [questionId]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await alunoApi.postSubmissaoAvaliacao({
        assessment_id: assessmentId,
        respostas,
      })
      setSubmetida(true)
    } catch {
      setError('Não foi possível submeter a avaliação.')
      setSubmitting(false)
    }
  }

  return (
    <div className="clop-pagina">
      <header className="clop-pagina__cabecalho">
        <a href="#/avaliacoes" className="clop-btn clop-btn--ghost">← Avaliações</a>
        <h1>{avaliacao.titulo}</h1>
      </header>

      <section className="clop-avaliacao-detalhe">
        <p className="clop-avaliacao__descricao">{avaliacao.descricao}</p>
        <div className="clop-avaliacao__meta">
          <span>{avaliacao.total_perguntas} perguntas</span>
          <span>Nota mínima para aprovação: {avaliacao.nota_aprovacao}</span>
          <span>Tentativas: {avaliacao.tentativas_usadas} / {avaliacao.tentativas_maximas}</span>
        </div>

        <form onSubmit={handleSubmit} className="clop-form-avaliacao">
          {avaliacao.perguntas?.map((p: any) => (
            <div key={p.id} className="clop-pergunta">
              <div className="clop-pergunta__enunciado">
                <strong>{p.ordem + 1}. {p.enunciado}</strong>
              </div>
              <div className="clop-pergunta__opcoes">
                {p.tipo === 'OPCAO_MULTIPLA' && p.opcoes ? (
                  p.opcoes.split('|').map((opcao: string, idx: number) => (
                    <label key={idx} className="clop-radio">
                      <input
                        type="radio"
                        name={`q_${p.id}`}
                        value={opcao.trim()}
                        checked={respostas[p.id] === opcao.trim()}
                        onChange={(e) => handleResposta(p.id, e.target.value)}
                      />
                      {opcao.trim()}
                    </label>
                  ))
                ) : (
                  <input
                    type="text"
                    className="clop-input"
                    value={respostas[p.id] || ''}
                    onChange={(e) => handleResposta(p.id, e.target.value)}
                    placeholder="Sua resposta…"
                  />
                )}
              </div>
            </div>
          ))}

          <div className="clop-avaliacao__acoes">
            <button type="submit" className="clop-btn clop-btn--primary" disabled={submitting}>
              {submitting ? 'Submetendo…' : 'Submeter avaliação'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}