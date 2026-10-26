import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react'
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  CircleAlert,
  Eye,
  EyeOff,
  LoaderCircle,
  LockKeyhole,
  Mail,
  Phone,
  ShieldCheck,
  UserRound,
  X,
} from 'lucide-react'
import { BrandMark } from '../components/BrandMark'
import { institution } from '../config/institution'
import { ApiError, authApi, type AuthUser } from '../lib/api'
import '../styles/auth.css'

type Mode = 'login' | 'register'

type AuthScreenProps = {
  mode: Mode
}

const PROVINCES = [
  'Bengo',
  'Benguela',
  'Bié',
  'Cabinda',
  'Cuando Cubango',
  'Cuanza Norte',
  'Cuanza Sul',
  'Cunene',
  'Huambo',
  'Huíla',
  'Luanda',
  'Lunda Norte',
  'Lunda Sul',
  'Malanje',
  'Moxico',
  'Namibe',
  'Uíge',
  'Zaire',
]

const INTRO_KEY = 'clop:intro-seen'

const ROLE_LABELS: Record<string, string> = {
  STUDENT: 'Aluno',
  INSTRUCTOR: 'Formador',
  EDITOR: 'Editor',
  FINANCE: 'Financeiro',
  ADMIN: 'Administrador',
  SUPERADMIN: 'Superadministrador',
}

function checksForPassword(password: string) {
  return [
    { label: 'Pelo menos 8 caracteres', ok: password.length >= 8 },
    { label: 'Contém uma letra', ok: /[A-Za-z]/.test(password) },
    { label: 'Contém um número', ok: /\d/.test(password) },
  ]
}

function passwordScore(password: string) {
  const checks = checksForPassword(password)
  let score = checks.filter((check) => check.ok).length
  if (password.length >= 12) score += 1
  if (/[^A-Za-z0-9]/.test(password)) score += 1
  return Math.min(score, 5)
}

function errorMessages(error: unknown): string[] {
  if (error instanceof ApiError) {
    return error.details.length > 0 ? error.details : [error.message]
  }
  return ['Ocorreu um erro inesperado. Tente novamente.']
}

function firstName(name: string) {
  return name.trim().split(/\s+/)[0] ?? name
}

export default function AuthScreen({ mode }: AuthScreenProps) {
  const [user, setUser] = useState<AuthUser | null>(() => authApi.cachedUser())
  const [validating, setValidating] = useState(
    () => authApi.hasSession() && !authApi.cachedUser(),
  )
  const [sessionWarning, setSessionWarning] = useState('')
  const [errors, setErrors] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [capsLock, setCapsLock] = useState(false)
  const [intro, setIntro] = useState(() => {
    try {
      return sessionStorage.getItem(INTRO_KEY) !== '1'
    } catch {
      return true
    }
  })
  const [introLeaving, setIntroLeaving] = useState(false)
  const stageVideoRef = useRef<HTMLVideoElement>(null)
  const introVideoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    document.title =
      mode === 'login'
        ? 'Entrar — CLOP Academia Digital'
        : 'Criar conta — CLOP Academia Digital'

    setErrors([])
    setLoading(false)
    setPassword('')
    setConfirm('')
    window.scrollTo({ top: 0, behavior: 'auto' })
  }, [mode])

  useEffect(() => {
    if (!authApi.hasSession()) {
      setValidating(false)
      return
    }

    let active = true

    authApi
      .me()
      .then((current) => {
        if (!active) return
        setUser(current)
        setSessionWarning('')
      })
      .catch((error: unknown) => {
        if (!active) return
        if (error instanceof ApiError && error.status === 401) {
          authApi.logout()
          setUser(null)
        } else {
          setSessionWarning(
            'Não foi possível confirmar a sessão com o servidor. Os dados apresentados podem estar desactualizados.',
          )
        }
      })
      .finally(() => {
        if (active) setValidating(false)
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    const video = stageVideoRef.current
    if (!video) return

    const seek = () => {
      video.currentTime = 4.25
    }
    const keepAmbient = () => {
      if (video.currentTime > 7.82) video.currentTime = 4.25
    }

    video.addEventListener('loadedmetadata', seek)
    video.addEventListener('timeupdate', keepAmbient)
    return () => {
      video.removeEventListener('loadedmetadata', seek)
      video.removeEventListener('timeupdate', keepAmbient)
    }
  }, [])

  const finishIntro = useCallback(() => {
    setIntroLeaving(true)
    try {
      sessionStorage.setItem(INTRO_KEY, '1')
    } catch {
      /* armazenamento indisponível — a introdução volta na próxima sessão */
    }
    window.setTimeout(() => setIntro(false), 900)
  }, [])

  useEffect(() => {
    if (!intro) return

    try {
      if (sessionStorage.getItem(INTRO_KEY) === '1') {
        setIntro(false)
        return
      }
    } catch {
      /* continuar com a introdução */
    }

    const timer = window.setTimeout(finishIntro, 5200)
    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') finishIntro()
    }
    window.addEventListener('keydown', onKeyDown)

    return () => {
      window.clearTimeout(timer)
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [intro, finishIntro])

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (loading) return

    const data = new FormData(event.currentTarget)
    const email = String(data.get('email') ?? '').trim()
    const secret = String(data.get('password') ?? '')
    const remember = data.get('remember') === 'on'

    setErrors([])
    setLoading(true)

    try {
      const response = await authApi.login({ email, password: secret }, remember)
      setUser(response.user)
      setSessionWarning('')
    } catch (error) {
      setErrors(errorMessages(error))
    } finally {
      setLoading(false)
    }
  }

  async function handleRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (loading) return

    const data = new FormData(event.currentTarget)
    const name = String(data.get('name') ?? '').trim()
    const email = String(data.get('email') ?? '').trim()
    const phone = String(data.get('phone') ?? '').trim()
    const province = String(data.get('province') ?? '')
    const secret = String(data.get('password') ?? '')
    const confirmation = String(data.get('confirm') ?? '')
    const terms = data.get('terms') === 'on'
    const remember = data.get('remember') === 'on'

    const problems: string[] = []

    if (name.length < 3) problems.push('Indique o nome completo (mínimo 3 caracteres).')
    if (!email) problems.push('Indique um endereço de e-mail.')
    if (secret !== confirmation) problems.push('As palavras-passe não coincidem.')
    for (const check of checksForPassword(secret)) {
      if (!check.ok && !problems.includes(check.label)) problems.push(check.label)
    }
    if (!terms) problems.push('É necessário aceitar os termos e a política de privacidade.')

    if (problems.length > 0) {
      setErrors(problems)
      return
    }

    setErrors([])
    setLoading(true)

    try {
      const response = await authApi.register(
        {
          nome_completo: name,
          email,
          telefone: phone || null,
          password: secret,
          aceite_termos: true,
          aceite_privacidade: true,
          provincia: province || null,
          cidade: null,
          objetivo: null,
        },
        remember,
      )
      setUser(response.user)
      setSessionWarning('')
    } catch (error) {
      setErrors(errorMessages(error))
    } finally {
      setLoading(false)
    }
  }

  function handlePasswordKey(event: KeyboardEvent<HTMLInputElement>) {
    setCapsLock(event.getModifierState('CapsLock'))
  }

  function signOut() {
    authApi.logout()
    setUser(null)
    setSessionWarning('')
    setErrors([])
  }

  const rules = checksForPassword(password)
  const score = passwordScore(password)
  const requiredOk = rules.every((rule) => rule.ok)
  const strengthLabel = ['Muito fraca', 'Fraca', 'Razoável', 'Boa', 'Forte', 'Excelente'][score]
  const mailtoSupport = `mailto:${institution.contacts.email}?subject=${encodeURIComponent(
    'Apoio ao acesso — CLOP Academia Digital',
  )}`

  return (
    <div className="auth">
      <aside className="auth-stage" aria-label="CLOP Academia Digital">
        <video
          ref={stageVideoRef}
          className="auth-stage__video"
          src="/brand/clop-brand-film.mp4"
          poster="/brand/clop-brand-poster.jpg"
          autoPlay
          muted
          playsInline
          preload="auto"
          aria-hidden="true"
        />
        <div className="auth-stage__grain" aria-hidden="true" />
        <div className="auth-stage__veil" aria-hidden="true" />

        <div className="auth-stage__top">
          <BrandMark theme="light" emblemSize={54} />
          <span className="auth-stage__descriptor">{institution.descriptor}</span>
        </div>

        <div className="auth-stage__copy">
          <p className="auth-stage__eyebrow">
            <span />
            Conhecimento que transforma
          </p>
          <p className="auth-stage__credo">
            Análise.
            <br />
            Estratégia.
            <br />
            <em>Resultados.</em>
          </p>
          <p className="auth-stage__note">
            Educação financeira, formação profissional e leitura de mercados — com rigor,
            responsabilidade e visão de futuro.
          </p>
        </div>

        <ul className="auth-stage__pillars">
          {institution.pillars.map((pillar) => (
            <li key={pillar}>
              <span aria-hidden="true">◆</span>
              {pillar}
            </li>
          ))}
        </ul>
      </aside>

      <main className="auth-main">
        <div className="auth-topbar">
          <a className="auth-back" href="#inicio">
            <ArrowLeft size={15} aria-hidden="true" />
            Portal institucional
          </a>
          <a className="auth-help" href={mailtoSupport}>
            Precisa de ajuda?
          </a>
        </div>

        {validating && !user ? (
          <section className="auth-card auth-card--loading" aria-live="polite">
            <LoaderCircle className="auth-spin" size={26} aria-hidden="true" />
            <p>A confirmar a sua sessão…</p>
          </section>
        ) : user ? (
          <section className="auth-card auth-card--session">
            <div className="auth-success-mark" aria-hidden="true">
              <Check size={26} strokeWidth={2.2} />
            </div>
            <p className="auth-eyebrow">
              <span />
              Sessão iniciada
            </p>
            <h1>Bem-vindo, {firstName(user.nome_completo)}.</h1>
            <p className="auth-lead">
              O seu acesso à CLOP Academia Digital está activo. Continue para o portal e
              acompanhe as próximas formações, conteúdos e iniciativas.
            </p>

            {sessionWarning && (
              <div className="auth-alert auth-alert--notice" role="status">
                <CircleAlert size={18} aria-hidden="true" />
                <div>
                  <p>{sessionWarning}</p>
                </div>
              </div>
            )}

            <dl className="auth-session">
              <div>
                <dt>E-mail</dt>
                <dd>{user.email}</dd>
              </div>
              <div>
                <dt>Perfil</dt>
                <dd>{ROLE_LABELS[user.role] ?? user.role}</dd>
              </div>
              {user.perfil_aluno?.provincia && (
                <div>
                  <dt>Província</dt>
                  <dd>{user.perfil_aluno.provincia}</dd>
                </div>
              )}
              <div>
                <dt>Estado</dt>
                <dd className="auth-session__state">
                  <span aria-hidden="true" />
                  {user.estado === 'ACTIVE' ? 'Conta activa' : user.estado}
                </dd>
              </div>
            </dl>

            <a className="auth-submit" href="#inicio">
              Explorar o portal
              <ArrowRight size={17} aria-hidden="true" />
            </a>
            <button className="auth-secondary" type="button" onClick={signOut}>
              Terminar sessão
            </button>
            <p className="auth-legal">
              Sessão protegida por autenticação CLOP. Não partilhe as suas credenciais.
            </p>
          </section>
        ) : (
          <section className="auth-card">
            <div className="auth-card__glow" aria-hidden="true" />

            <div className="auth-tabs" role="tablist" aria-label="Acesso à conta">
              <a
                href="#/entrar"
                role="tab"
                aria-selected={mode === 'login'}
                className={mode === 'login' ? 'is-active' : ''}
              >
                Entrar
              </a>
              <a
                href="#/registar"
                role="tab"
                aria-selected={mode === 'register'}
                className={mode === 'register' ? 'is-active' : ''}
              >
                Criar conta
              </a>
              <span className={`auth-tabs__indicator auth-tabs__indicator--${mode}`} />
            </div>

            <p className="auth-eyebrow">
              <span />
              {mode === 'login' ? 'Acesso de aluno' : 'Registo de aluno'}
            </p>
            <h1>{mode === 'login' ? 'Entrar na Academia' : 'Criar a tua conta'}</h1>
            <p className="auth-lead">
              {mode === 'login'
                ? 'Retome a sua formação, consulte o progresso e aceda aos conteúdos da CLOP.'
                : 'Comece agora. Leva menos de um minuto e dá acesso ao percurso formativo CLOP.'}
            </p>

            {errors.length > 0 && (
              <div className="auth-alert" role="alert">
                <CircleAlert size={18} aria-hidden="true" />
                <div>
                  {errors.map((message) => (
                    <p key={message}>{message}</p>
                  ))}
                </div>
              </div>
            )}

            {mode === 'login' ? (
              <form className="auth-form" onSubmit={handleLogin}>
                <div className="auth-fields">
                  <label className="auth-field auth-field--wide">
                    <span>E-mail</span>
                    <span className="auth-input">
                      <Mail size={17} aria-hidden="true" />
                      <input
                        name="email"
                        type="email"
                        autoComplete="email"
                        placeholder="nome@exemplo.com"
                        required
                      />
                    </span>
                  </label>

                  <label className="auth-field auth-field--wide">
                    <span>Palavra-passe</span>
                    <span className="auth-input">
                      <LockKeyhole size={17} aria-hidden="true" />
                      <input
                        name="password"
                        type={showPassword ? 'text' : 'password'}
                        autoComplete="current-password"
                        placeholder="A sua palavra-passe"
                        required
                        onKeyDown={handlePasswordKey}
                        onKeyUp={handlePasswordKey}
                      />
                      <button
                        className="auth-reveal"
                        type="button"
                        onClick={() => setShowPassword((visible) => !visible)}
                        aria-label={showPassword ? 'Ocultar palavra-passe' : 'Mostrar palavra-passe'}
                      >
                        {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                      </button>
                    </span>
                  </label>
                </div>

                {capsLock && (
                  <p className="auth-caps" role="status">
                    <CircleAlert size={14} aria-hidden="true" /> Caps Lock está activado.
                  </p>
                )}

                <div className="auth-row">
                  <label className="auth-check">
                    <input name="remember" type="checkbox" defaultChecked />
                    <span>Manter sessão neste dispositivo</span>
                  </label>
                  <a className="auth-inline-link" href={mailtoSupport}>
                    Esqueceu-se?
                  </a>
                </div>

                <button className="auth-submit" type="submit" disabled={loading}>
                  {loading ? (
                    <>
                      <LoaderCircle className="auth-spin" size={18} aria-hidden="true" />
                      A entrar…
                    </>
                  ) : (
                    <>
                      Entrar na Academia
                      <ArrowRight size={17} aria-hidden="true" />
                    </>
                  )}
                </button>

                <p className="auth-switch">
                  Ainda não tem conta? <a href="#/registar">Criar conta</a>
                </p>
              </form>
            ) : (
              <form className="auth-form" onSubmit={handleRegister}>
                <div className="auth-fields">
                  <label className="auth-field auth-field--wide">
                    <span>Nome completo</span>
                    <span className="auth-input">
                      <UserRound size={17} aria-hidden="true" />
                      <input
                        name="name"
                        type="text"
                        autoComplete="name"
                        placeholder="O seu nome completo"
                        minLength={3}
                        maxLength={140}
                        required
                      />
                    </span>
                  </label>

                  <label className="auth-field auth-field--wide">
                    <span>E-mail</span>
                    <span className="auth-input">
                      <Mail size={17} aria-hidden="true" />
                      <input
                        name="email"
                        type="email"
                        autoComplete="email"
                        placeholder="nome@exemplo.com"
                        required
                      />
                    </span>
                  </label>

                  <label className="auth-field">
                    <span>
                      Telefone <em>(opcional)</em>
                    </span>
                    <span className="auth-input">
                      <Phone size={17} aria-hidden="true" />
                      <input
                        name="phone"
                        type="tel"
                        autoComplete="tel"
                        placeholder="+244 9xx xxx xxx"
                        maxLength={30}
                      />
                    </span>
                  </label>

                  <label className="auth-field">
                    <span>
                      Província <em>(opcional)</em>
                    </span>
                    <span className="auth-input auth-input--select">
                      <select name="province" defaultValue="">
                        <option value="">Seleccionar</option>
                        {PROVINCES.map((province) => (
                          <option key={province} value={province}>
                            {province}
                          </option>
                        ))}
                      </select>
                      <ChevronDown size={16} aria-hidden="true" />
                    </span>
                  </label>

                  <label className="auth-field auth-field--wide">
                    <span>Palavra-passe</span>
                    <span className="auth-input">
                      <LockKeyhole size={17} aria-hidden="true" />
                      <input
                        name="password"
                        type={showPassword ? 'text' : 'password'}
                        autoComplete="new-password"
                        placeholder="Crie uma palavra-passe segura"
                        minLength={8}
                        maxLength={128}
                        required
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        onKeyDown={handlePasswordKey}
                        onKeyUp={handlePasswordKey}
                      />
                      <button
                        className="auth-reveal"
                        type="button"
                        onClick={() => setShowPassword((visible) => !visible)}
                        aria-label={showPassword ? 'Ocultar palavra-passe' : 'Mostrar palavra-passe'}
                      >
                        {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                      </button>
                    </span>
                  </label>

                  <div className="auth-strength" aria-live="polite">
                    <div className="auth-strength__bars" aria-hidden="true">
                      {[1, 2, 3, 4, 5].map((bar) => (
                        <span
                          key={bar}
                          className={bar <= score ? `is-on is-level-${score}` : ''}
                        />
                      ))}
                    </div>
                    <span>{password ? strengthLabel : 'A força da palavra-passe'}</span>
                  </div>

                  <ul className="auth-rules">
                    {rules.map((rule) => (
                      <li key={rule.label} className={rule.ok ? 'is-ok' : ''}>
                        <Check size={13} aria-hidden="true" />
                        {rule.label}
                      </li>
                    ))}
                  </ul>

                  <label className="auth-field auth-field--wide">
                    <span>Confirmar palavra-passe</span>
                    <span className="auth-input">
                      <ShieldCheck size={17} aria-hidden="true" />
                      <input
                        name="confirm"
                        type={showConfirm ? 'text' : 'password'}
                        autoComplete="new-password"
                        placeholder="Repita a palavra-passe"
                        required
                        value={confirm}
                        onChange={(event) => setConfirm(event.target.value)}
                      />
                      <button
                        className="auth-reveal"
                        type="button"
                        onClick={() => setShowConfirm((visible) => !visible)}
                        aria-label={
                          showConfirm ? 'Ocultar confirmação' : 'Mostrar confirmação'
                        }
                      >
                        {showConfirm ? <EyeOff size={17} /> : <Eye size={17} />}
                      </button>
                    </span>
                  </label>
                  {confirm.length > 0 && confirm !== password && (
                    <p className="auth-caps auth-caps--wide" role="status">
                      <CircleAlert size={14} aria-hidden="true" /> As palavras-passe não
                      coincidem.
                    </p>
                  )}
                </div>

                {capsLock && (
                  <p className="auth-caps" role="status">
                    <CircleAlert size={14} aria-hidden="true" /> Caps Lock está activado.
                  </p>
                )}

                <div className="auth-row">
                  <label className="auth-check">
                    <input name="remember" type="checkbox" defaultChecked />
                    <span>Manter sessão neste dispositivo</span>
                  </label>
                </div>

                <details className="auth-terms">
                  <summary>Termos e política de privacidade</summary>
                  <p>
                    Ao criar conta, os seus dados são utilizados para gerir o acesso à
                    plataforma, inscrições e comunicações institucionais. Os conteúdos
                    financeiros têm finalidade educativa e não constituem aconselhamento
                    personalizado.
                  </p>
                </details>

                <label className="auth-check auth-check--terms">
                  <input name="terms" type="checkbox" required />
                  <span>
                    Li e aceito os termos de utilização e a política de privacidade da CLOP
                    Academia Digital.
                  </span>
                </label>

                <button
                  className="auth-submit"
                  type="submit"
                  disabled={loading || !requiredOk}
                >
                  {loading ? (
                    <>
                      <LoaderCircle className="auth-spin" size={18} aria-hidden="true" />
                      A criar conta…
                    </>
                  ) : (
                    <>
                      Criar conta
                      <ArrowRight size={17} aria-hidden="true" />
                    </>
                  )}
                </button>

                <p className="auth-switch">
                  Já tem conta? <a href="#/entrar">Entrar</a>
                </p>
              </form>
            )}

            <p className="auth-legal">
              CLOP Academia Digital, LDA. · Luanda, Angola
              <br />
              Acesso protegido. Nunca partilhe as suas credenciais.
            </p>
          </section>
        )}

        <footer className="auth-foot">
          <span>© {new Date().getFullYear()} CLOP Academia Digital</span>
          <span className="auth-foot__credo">Análise · Estratégia · Resultados</span>
        </footer>
      </main>

      {intro && (
        <div
          className={`clop-intro${introLeaving ? ' is-leaving' : ''}`}
          role="dialog"
          aria-modal="true"
          aria-label="Introdução CLOP Academia Digital"
        >
          <video
            ref={introVideoRef}
            className="clop-intro__video"
            src="/brand/clop-brand-film.mp4"
            poster="/brand/clop-brand-poster.jpg"
            autoPlay
            muted
            playsInline
            preload="auto"
            onLoadedMetadata={(event) => {
              event.currentTarget.currentTime = 3.1
              void event.currentTarget.play().catch(() => undefined)
            }}
            onEnded={finishIntro}
          />
          <div className="clop-intro__scrim" aria-hidden="true" />
          <div className="clop-intro__content">
            <BrandMark theme="light" emblemSize={62} href="#/entrar" />
            <p>Confiança. Disciplina. Lucro.</p>
          </div>
          <button className="clop-intro__skip" type="button" onClick={finishIntro}>
            Saltar introdução
            <X size={15} aria-hidden="true" />
          </button>
          <div className="clop-intro__progress" aria-hidden="true">
            <span />
          </div>
        </div>
      )}
    </div>
  )
}
