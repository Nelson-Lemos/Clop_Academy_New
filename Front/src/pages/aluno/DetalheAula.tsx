import { useEffect, useState } from 'react'
import { alunoApi } from '../../lib/api'

export default function DetalheAula({ courseId, lessonId }: { courseId: number; lessonId: number }) {
  const [aula, setAula] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    alunoApi.getDetalheAula(courseId, lessonId)
      .then((data) => { if (active) setAula(data) })
      .catch(() => { if (active) setError('Não foi possível carregar a aula.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [courseId, lessonId])

  if (loading) return <div className="clop-loader">A carregar…</div>
  if (error) return <div className="clop-erro">{error}</div>
  if (!aula) return null

  return (
    <div className="clop-pagina">
      <header className="clop-pagina__cabecalho">
        <a href={`#/cursos/${courseId}`} className="clop-btn clop-btn--ghost">← Voltar ao curso</a>
        <h1>{aula.titulo}</h1>
      </header>

      <section className="clop-aula-detalhe">
        <div className="clop-aula__conteudo">
          <p className="clop-aula__tipo">{aula.tipo}</p>
          <p className="clop-aula__duracao">{aula.duracao_minutos} min</p>
          {aula.descricao && <div className="clop-aula__descricao">{aula.descricao}</div>}
          {aula.conteudo && <div className="clop-aula__conteudo-texto" dangerouslySetInnerHTML={{ __html: aula.conteudo }} />}
        </div>

        {aula.video_url && (
          <div className="clop-aula__video">
            <video controls className="clop-video">
              <source src={aula.video_url} type="video/mp4" />
              Seu navegador não suporta vídeo.
            </video>
          </div>
        )}

        {aula.link_live && (
          <div className="clop-aula__live">
            <a href={aula.link_live} target="_blank" rel="noopener noreferrer" className="clop-btn clop-btn--primary">
              Acessar aula ao vivo
            </a>
            {aula.data_live && <p>Data ao vivo: {new Date(aula.data_live).toLocaleString()}</p>}
          </div>
        )}

        {aula.materiais?.length && (
          <div className="clop-aula__materiais">
            <h3>Materiais</h3>
            <ul>
              {aula.materiais.map((m: any) => (
                <li key={m.id}>
                  <a href={m.url} target="_blank" rel="noopener noreferrer" className="clop-link-material">
                    {m.titulo} ({m.tipo})
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="clop-aula__progresso">
          <div className="clop-progresso-info">
            <span>{aula.percentagem_video}% assistido</span>
            <span>{aula.concluida ? 'Concluída' : 'Pendente'}</span>
          </div>
          <button className="clop-btn clop-btn--primary" onClick={() => marcarConcluida()}>
            {aula.concluida ? 'Marcar como pendente' : 'Marcar como concluída'}
          </button>
        </div>
      </section>
    </div>
  )

  async function marcarConcluida() {
    try {
      await alunoApi.postProgresso(courseId, {
        lesson_id: lessonId,
        concluida: !aula.concluida,
        percentagem_video: aula.concluida ? 0 : 100,
      })
      setAula((prev: any) => ({ ...prev, concluida: !prev.concluida, percentagem_video: prev.concluida ? 0 : 100 }))
    } catch {
      alert('Não foi possível atualizar o progresso.')
    }
  }
}