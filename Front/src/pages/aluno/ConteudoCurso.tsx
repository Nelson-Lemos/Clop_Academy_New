import { useEffect, useState } from 'react'
import { alunoApi, type ConteudoCurso } from '../../lib/api'

export default function ConteudoCurso({ courseId }: { courseId: number }) {
  const [conteudo, setConteudo] = useState<ConteudoCurso | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    alunoApi.getConteudoCurso(courseId)
      .then((data) => { if (active) setConteudo(data) })
      .catch(() => { if (active) setError('Não foi possível carregar o conteúdo do curso.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [courseId])

  if (loading) return <div className="clop-loader">A carregar…</div>
  if (error) return <div className="clop-erro">{error}</div>
  if (!conteudo) return null

  const { curso, inscricao, modulos } = conteudo

  return (
    <div className="clop-pagina">
      <header className="clop-pagina__cabecalho">
        <div className="clop-pagina__titulo">
          <h1>{curso.nome}</h1>
          <p>{inscricao.percentagem_progresso}% concluído · {inscricao.estado}</p>
        </div>
        <a href="#/dashboard" className="clop-btn clop-btn--ghost">← Dashboard</a>
      </header>

      <section className="clop-curso-conteudo">
        <div className="clop-curso-resumo">
          <div className="clop-info-item">
            <strong>Modalidade:</strong> {curso.modalidade}
          </div>
          <div className="clop-info-item">
            <strong>Duração:</strong> {curso.duracao_horas}h
          </div>
          <div className="clop-info-item">
            <strong>Progresso:</strong> {inscricao.percentagem_progresso}%
          </div>
        </div>

        <div className="clop-modulos">
          {modulos.map((modulo) => (
            <div key={modulo.id} className="clop-modulo">
              <div className="clop-modulo__cabecalho" onClick={() => {}}>
                <h3>{modulo.titulo}</h3>
                <span>{modulo.aulas.filter((a) => a.concluida).length} / {modulo.aulas.length} concluídas</span>
              </div>
              <div className="clop-modulo__aulas">
                {modulo.aulas.map((aula) => (
                  <a
                    key={aula.id}
                    href={`#/aulas/${courseId}/${aula.id}`}
                    className={`clop-item-aula ${aula.concluida ? 'concluida' : ''}`}
                  >
                    <span className={`clop-status-aula ${aula.concluida ? 'concluida' : 'pendente'}`}>
                      {aula.concluida ? '✓' : '○'}
                    </span>
                    <span>{aula.titulo}</span>
                    <span className="clop-duracao-aula">{aula.duracao_minutos} min</span>
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}