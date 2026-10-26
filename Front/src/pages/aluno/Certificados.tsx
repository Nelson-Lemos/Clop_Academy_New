import { useEffect, useState } from 'react'
import { Award, BadgeCheck, CalendarDays, GraduationCap, Hash } from 'lucide-react'
import { alunoApi, type CertificadoAluno } from '../../lib/api'
import { PageHeader } from '../../components/PageHeader'
import { EmptyState } from '../../components/EmptyState'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { estadoLabel, estadoTone, formatDate } from '../../lib/labels'

export default function Certificados() {
  const [certificados, setCertificados] = useState<CertificadoAluno[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    alunoApi
      .getCertificados()
      .then((data) => {
        if (active) setCertificados(data)
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar os certificados.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadKey])

  return (
    <>
      <PageHeader
        eyebrow="Certificação"
        title="Certificados"
        description="Certificados emitidos após a conclusão dos requisitos de cada curso."
      />

      {loading && <LoadingState label="A carregar certificados…" />}
      {!loading && error && <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />}

      {!loading && !error && certificados.length === 0 && (
        <EmptyState
          icon={Award}
          title="Ainda não tem certificados"
          description="Conclua um curso e cumpra os requisitos de avaliação para solicitar a emissão do certificado."
          action={
            <a className="btn btn--gold btn--sm" href="#/inscricoes">
              Ver os meus cursos
            </a>
          }
        />
      )}

      {!loading && !error && certificados.length > 0 && (
        <div className="cert-grid">
          {certificados.map((certificado) => (
            <article key={certificado.id} className="cert-card">
              <span className="cert-card__ribbon" aria-hidden="true" />
              <div className="cert-card__head">
                <span className="cert-card__seal" aria-hidden="true">
                  <BadgeCheck size={22} />
                </span>
                <span className={`badge badge--${estadoTone(certificado.estado)}`}>
                  {estadoLabel(certificado.estado)}
                </span>
              </div>

              <p className="cert-card__eyebrow">CLOP Academia Digital</p>
              <h3 className="cert-card__title">{certificado.curso_nome || 'Curso'}</h3>

              <dl className="cert-card__meta">
                <div>
                  <dt>
                    <GraduationCap size={14} aria-hidden="true" /> Aluno
                  </dt>
                  <dd>{certificado.aluno_nome || '—'}</dd>
                </div>
                <div>
                  <dt>
                    <CalendarDays size={14} aria-hidden="true" /> Emitido em
                  </dt>
                  <dd>{formatDate(certificado.emitido_em)}</dd>
                </div>
                <div>
                  <dt>
                    <Award size={14} aria-hidden="true" /> Nota final
                  </dt>
                  <dd>{certificado.nota_final ?? '—'}</dd>
                </div>
              </dl>

              <div className="cert-code">
                <Hash size={14} aria-hidden="true" />
                <span className="mono">{certificado.codigo}</span>
              </div>
            </article>
          ))}
        </div>
      )}
    </>
  )
}
