import { useEffect, useState } from 'react'
import AcademyHome from './pages/AcademyHome'
import AuthScreen from './pages/AuthScreen'
import AlunoDashboard from './pages/aluno/AlunoDashboard'
import MinhasInscricoes from './pages/aluno/MinhasInscricoes'
import ConteudoCurso from './pages/aluno/ConteudoCurso'
import DetalheAula from './pages/aluno/DetalheAula'
import Avaliacoes from './pages/aluno/Avaliacoes'
import DetalheAvaliacao from './pages/aluno/DetalheAvaliacao'
import Pagamentos from './pages/aluno/Pagamentos'
import Certificados from './pages/aluno/Certificados'
import Notificacoes from './pages/aluno/Notificacoes'
import Perfil from './pages/aluno/Perfil'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminCursos from './pages/admin/AdminCursos'
import './styles/brand.css'
import { useAuth } from './contexts/AuthContext'

type Route =
  | 'home'
  | 'login'
  | 'register'
  | 'dashboard'
  | 'inscricoes'
  | 'curso-conteudo'
  | 'curso-aula'
  | 'avaliacoes'
  | 'avaliacao-detalhe'
  | 'pagamentos'
  | 'certificados'
  | 'notificacoes'
  | 'perfil'
  | 'admin-dashboard'
  | 'admin-cursos'

const HOME_TITLE = 'CLOP Academia Digital — Educação Financeira & Mercados'

function parseHash(): { route: Route; params: Record<string, string> } {
  const hash = window.location.hash.replace(/^#\/?/, '').toLowerCase()
  const [path, query] = hash.split('?')
  const segments = path.split('/').filter(Boolean)

  const params: Record<string, string> = {}
  if (query) {
    new URLSearchParams(query).forEach((value, key) => {
      params[key] = value
    })
  }

  if (segments.length === 0) return { route: 'home', params }
  if (segments[0] === 'entrar') return { route: 'login', params }
  if (segments[0] === 'registar') return { route: 'register', params }
  if (segments[0] === 'dashboard') return { route: 'dashboard', params }
  if (segments[0] === 'inscricoes') return { route: 'inscricoes', params }
  if (segments[0] === 'cursos' && segments.length === 2)
    return { route: 'curso-conteudo', params: { ...params, id: segments[1] } }
  if (segments[0] === 'aulas' && segments.length === 3)
    return {
      route: 'curso-aula',
      params: { ...params, courseId: segments[1], lessonId: segments[2] },
    }
  if (segments[0] === 'avaliacoes' && segments.length === 1)
    return { route: 'avaliacoes', params }
  if (segments[0] === 'avaliacoes' && segments.length === 2)
    return { route: 'avaliacao-detalhe', params: { ...params, id: segments[1] } }
  if (segments[0] === 'pagamentos') return { route: 'pagamentos', params }
  if (segments[0] === 'certificados') return { route: 'certificados', params }
  if (segments[0] === 'notificacoes') return { route: 'notificacoes', params }
  if (segments[0] === 'perfil') return { route: 'perfil', params }

  // Admin
  if (segments[0] === 'admin') {
    if (segments[1] === 'dashboard') return { route: 'admin-dashboard', params }
    if (segments[1] === 'cursos') return { route: 'admin-cursos', params }
  }

  return { route: 'home', params }
}

function requiresAuth(route: Route): boolean {
  const publicRoutes = ['home', 'login', 'register']
  return !publicRoutes.includes(route)
}

export default function App() {
  const { user, loading, isAuthenticated, logout } = useAuth()
  const [routeState, setRouteState] = useState(parseHash())

  useEffect(() => {
    const onHashChange = () => setRouteState(parseHash())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  useEffect(() => {
    if (routeState.route !== 'home') return

    document.title = HOME_TITLE
    const hash = window.location.hash
    if (hash && !hash.startsWith('#/')) {
      const id = hash.slice(1)
      const frame = window.requestAnimationFrame(() => {
        document.getElementById(id)?.scrollIntoView({ behavior: 'auto', block: 'start' })
      })
      return () => window.cancelAnimationFrame(frame)
    }
  }, [routeState.route])

  if (loading) {
    return (
      <div className="clop-page clop-page--center">
        <div className="clop-loader">A carregar sessão…</div>
      </div>
    )
  }

  const { route } = routeState

  // Redireciona para login se tentar aceder a rota privada sem sessão
  if (requiresAuth(route) && !isAuthenticated) {
    window.location.hash = '#/entrar'
    return null
  }

  // Redireciona para dashboard se usuário autenticado tentar ir para login/registro
  if ((route === 'login' || route === 'register') && isAuthenticated) {
    window.location.hash = '#/dashboard'
    return null
  }

  // Rotas públicas
  if (route === 'home') return <AcademyHome onLogout={logout} />
  if (route === 'login') return <AuthScreen mode="login" />
  if (route === 'register') return <AuthScreen mode="register" />

  // Rotas do aluno
  if (route === 'dashboard') return <AlunoDashboard user={user!} />
  if (route === 'inscricoes') return <MinhasInscricoes />
  if (route === 'curso-conteudo')
    return <ConteudoCurso courseId={Number(routeState.params.id)} />
  if (route === 'curso-aula')
    return (
      <DetalheAula
        courseId={Number(routeState.params.courseId)}
        lessonId={Number(routeState.params.lessonId)}
      />
    )
  if (route === 'avaliacoes') return <Avaliacoes />
  if (route === 'avaliacao-detalhe')
    return <DetalheAvaliacao assessmentId={Number(routeState.params.id)} />
  if (route === 'pagamentos') return <Pagamentos />
  if (route === 'certificados') return <Certificados />
  if (route === 'notificacoes') return <Notificacoes />
  if (route === 'perfil') return <Perfil />

  // Rotas de admin
  if (route === 'admin-dashboard') return <AdminDashboard user={user!} />
  if (route === 'admin-cursos') return <AdminCursos />

  return <AcademyHome onLogout={logout} />
}
