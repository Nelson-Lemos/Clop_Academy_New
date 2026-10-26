import { useEffect, useState } from 'react'
import { alunoApi, type InscricaoAluno } from '../../lib/api'

export default function MinhasInscricoes() {
  const [inscricoes, setInscricoes] = useState<InscricaoAluno[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    alunoApi.getInscricoes()
      .then((data) => { if (active) setInscricoes(data) })
      .catch(() => { if (active) setError('Não foi possível carregar as inscrições.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  if (loading) return <div className="clop-loader">A carregar…</div>
  if (error) return <div className="clop-erro">{error}</div>

  return (
    <div className="clop-pagina">
      <header className="clop-pagina__cabecalho">
        <h1>Minhas Inscrições</h1>
        <a href="#/dashboard" className="clop-btn clop-btn--ghost">← Voltar</a>
      </header>

      {inscricoes.length === 0 ? (
        <div className="clop-vazio">
          <p>Nenhuma inscrição encontrada.</p>
        </div>
      ) : (
        <div className="clop-tabela">
          <table>
            <thead>
              <tr>
                <th>Curso</th>
                <th>Estado</th>
                <th>Progresso</th>
                <th>Aulas</th>
                <th>Próxima aula</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {inscricoes.map((i) => (
                <tr key={i.id} className="clop-linha-inscricao">
                  <td>
                    <strong>{i.curso_nome}</strong>
                    <span className="clop-destaque-secundario">{i.curso_modalidade} · {i.curso_duracao_horas}h</span>
                  </td>
                  <td>
                    <span className={`clop-badge clop-badge--${i.estado.toLowerCase()}`}>{i.estado}</span>
                  </td>
                  <td>
                    <div className="clop-progresso-compacto">
                      <div className="clop-progresso__label">
                        <span>{i.percentagem_progresso}%</span>
                      </div>
                      <div className="clop-progresso__barra">
                        <div className="clop-progresso__enchimento" style={{ width: `${Math.min(i.percentagem_progresso, 100)}%` }} />
                      </div>
                    </div>
                  </td>
                  <td>{i.aulas_concluidas} / {i.total_aulas}</td>
                  <td>{i.proxima_aula || '—'}</td>
                  <td>
                    <a href={`#/cursos/${i.course_id}`} className="clop-btn clop-btn--primary clop-btn--small">
                      Acessar curso
                    </a>
                    {i.certificado_disponivel && (
                      <a href="#/certificados" className="clop-btn clop-btn--outline clop-btn--small">Certificado</a>
                    )}
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