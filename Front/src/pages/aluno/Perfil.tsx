import { useEffect, useState } from 'react'
import {
  AtSign,
  Briefcase,
  Building2,
  CalendarDays,
  CheckCircle2,
  Link2,
  LogOut,
  Mail,
  MapPin,
  Phone,
  ShieldCheck,
  Sparkles,
  UserRound,
} from 'lucide-react'
import { authApi, type AuthUser } from '../../lib/api'
import { useAuth } from '../../contexts/AuthContext'
import { PageHeader } from '../../components/PageHeader'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { estadoLabel, estadoTone, formatDate, initials, roleLabel } from '../../lib/labels'

export default function Perfil() {
  const { logout } = useAuth()
  const [perfil, setPerfil] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    authApi
      .me()
      .then((data) => {
        if (active) setPerfil(data)
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar o perfil.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadKey])

  const sair = () => {
    logout()
    window.location.hash = '#/entrar'
  }

  if (loading) return <LoadingState label="A carregar perfil…" />
  if (error) return <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />
  if (!perfil) return null

  const aluno = perfil.perfil_aluno

  return (
    <>
      <PageHeader
        eyebrow="Conta"
        title="Perfil"
        description="Consulte os dados da sua conta e o perfil de aprendizagem."
        actions={
          <button type="button" className="btn btn--ghost btn--sm" onClick={sair}>
            <LogOut size={15} aria-hidden="true" />
            Terminar sessão
          </button>
        }
      />

      <section className="profile-hero">
        <div className="profile-hero__pattern" aria-hidden="true" />
        <div className="profile-hero__main">
          <span className="profile-avatar" aria-hidden="true">
            {initials(perfil.nome_completo || perfil.email)}
          </span>
          <div className="profile-hero__text">
            <h2>{perfil.nome_completo || 'Utilizador CLOP'}</h2>
            <p>
              <Mail size={14} aria-hidden="true" />
              {perfil.email}
            </p>
            <div className="profile-hero__badges">
              <span className="badge badge--gold">{roleLabel(perfil.role)}</span>
              <span className={`badge badge--${estadoTone(perfil.estado)}`}>
                {estadoLabel(perfil.estado)}
              </span>
              {perfil.email_verificado_em && (
                <span className="badge badge--success">
                  <CheckCircle2 size={13} aria-hidden="true" />
                  E-mail verificado
                </span>
              )}
            </div>
          </div>
        </div>
        <dl className="profile-hero__stats">
          <div>
            <dt>Membro desde</dt>
            <dd>{formatDate(perfil.criado_em)}</dd>
          </div>
          <div>
            <dt>Permissões</dt>
            <dd>{perfil.permissoes?.length ?? 0}</dd>
          </div>
        </dl>
      </section>

      <div className="profile-grid">
        <section className="app-card">
          <div className="app-card__header">
            <h3>Dados pessoais</h3>
            <UserRound size={17} aria-hidden="true" />
          </div>
          <dl className="detail-list">
            <DetailRow icon={Mail} label="E-mail" value={perfil.email} />
            <DetailRow icon={Phone} label="Telefone" value={perfil.telefone} />
            <DetailRow icon={MapPin} label="Província" value={aluno?.provincia} />
            <DetailRow icon={CalendarDays} label="Registo" value={formatDate(perfil.criado_em)} />
          </dl>
        </section>

        <section className="app-card">
          <div className="app-card__header">
            <h3>Perfil de aluno</h3>
            <Briefcase size={17} aria-hidden="true" />
          </div>
          <dl className="detail-list">
            <DetailRow icon={Briefcase} label="Profissão" value={aluno?.profissao} />
            <DetailRow icon={Building2} label="Empresa" value={aluno?.empresa} />
            <DetailRow icon={MapPin} label="Cidade" value={aluno?.cidade} />
            <DetailRow icon={Sparkles} label="Área de interesse" value={aluno?.area_interesse} />
            <DetailRow icon={AtSign} label="Nível de educação" value={aluno?.nivel_educacao} />
            <DetailRow icon={Link2} label="LinkedIn" value={aluno?.linkedin} />
          </dl>
        </section>

        <section className="app-card profile-grid__wide">
          <div className="app-card__header">
            <h3>Objetivo e apresentação</h3>
            <Sparkles size={17} aria-hidden="true" />
          </div>
          <div className="profile-about">
            <div>
              <span className="profile-about__label">Objetivo</span>
              <p>{aluno?.objetivo || 'Ainda não indicou um objetivo.'}</p>
            </div>
            <div>
              <span className="profile-about__label">Biografia</span>
              <p>{aluno?.biografia || 'Ainda não preencheu a biografia.'}</p>
            </div>
          </div>
        </section>

        <section className="app-card profile-grid__wide">
          <div className="app-card__header">
            <h3>Estado da conta</h3>
            <ShieldCheck size={17} aria-hidden="true" />
          </div>
          <dl className="detail-list detail-list--inline">
            <DetailRow icon={ShieldCheck} label="Estado" value={estadoLabel(perfil.estado)} />
            <DetailRow
              icon={Mail}
              label="Verificação de e-mail"
              value={perfil.email_verificado_em ? formatDate(perfil.email_verificado_em) : 'Não verificado'}
            />
            <DetailRow
              icon={CheckCircle2}
              label="Termos aceites"
              value={perfil.aceite_termos_em ? formatDate(perfil.aceite_termos_em) : 'Não registado'}
            />
            <DetailRow
              icon={Sparkles}
              label="Newsletter"
              value={aluno?.newsletter_inscrito ? 'Subscrito' : 'Não subscrito'}
            />
          </dl>
        </section>
      </div>
    </>
  )
}

function DetailRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Mail
  label: string
  value?: string | null
}) {
  return (
    <div className="detail-list__row">
      <dt>
        <Icon size={15} aria-hidden="true" />
        {label}
      </dt>
      <dd>{value || '—'}</dd>
    </div>
  )
}
