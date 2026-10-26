import { useEffect, useState, type ReactNode } from 'react'
import {
  Award,
  BarChart3,
  Bell,
  BookOpen,
  ChevronRight,
  ClipboardList,
  CreditCard,
  ExternalLink,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  User,
  X,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { BrandMark } from './BrandMark'
import type { AuthUser } from '../lib/api'
import { initials, roleLabel } from '../lib/labels'

type NavItem = {
  href: string
  label: string
  icon: LucideIcon
  routes: string[]
}

const STUDENT_NAV: NavItem[] = [
  { href: '#/dashboard', label: 'Visão geral', icon: LayoutDashboard, routes: ['dashboard'] },
  { href: '#/inscricoes', label: 'Meus cursos', icon: BookOpen, routes: ['inscricoes', 'curso-conteudo', 'curso-aula'] },
  { href: '#/avaliacoes', label: 'Avaliações', icon: ClipboardList, routes: ['avaliacoes', 'avaliacao-detalhe'] },
  { href: '#/certificados', label: 'Certificados', icon: Award, routes: ['certificados'] },
  { href: '#/pagamentos', label: 'Pagamentos', icon: CreditCard, routes: ['pagamentos'] },
  { href: '#/notificacoes', label: 'Notificações', icon: Bell, routes: ['notificacoes'] },
  { href: '#/perfil', label: 'Perfil', icon: User, routes: ['perfil'] },
]

const ADMIN_DASHBOARD: NavItem = {
  href: '#/admin/dashboard',
  label: 'Painel de gestão',
  icon: BarChart3,
  routes: ['admin-dashboard'],
}

const ADMIN_CURSOS: NavItem = {
  href: '#/admin/cursos',
  label: 'Gestão de cursos',
  icon: GraduationCap,
  routes: ['admin-cursos'],
}

const PERFIL_NAV: NavItem = { href: '#/perfil', label: 'Perfil', icon: User, routes: ['perfil'] }

const ROUTE_SECTIONS: Record<string, string> = {
  dashboard: 'Área do aluno',
  inscricoes: 'Área do aluno',
  'curso-conteudo': 'Área do aluno',
  'curso-aula': 'Área do aluno',
  avaliacoes: 'Área do aluno',
  'avaliacao-detalhe': 'Área do aluno',
  certificados: 'Área do aluno',
  pagamentos: 'Área do aluno',
  notificacoes: 'Área do aluno',
  perfil: 'Conta',
  'admin-dashboard': 'Administração',
  'admin-cursos': 'Administração',
}

const ADMIN_ROLES = ['ADMIN', 'SUPERADMIN', 'EDITOR', 'FINANCE']

type AppShellProps = {
  user: AuthUser
  route: string
  onLogout: () => void
  children: ReactNode
}

/**
 * Estrutura da plataforma autenticada: navegação lateral persistente,
 * barra superior contextual e área de conteúdo.
 */
export function AppShell({ user, route, onLogout, children }: AppShellProps) {
  const [navOpen, setNavOpen] = useState(false)

  const isStudent = user.role.toUpperCase() === 'STUDENT'
  const canSeeAdmin = ADMIN_ROLES.includes(user.role.toUpperCase())
  const canSeeCourses = canSeeAdmin || user.role.toUpperCase() === 'INSTRUCTOR'

  const navigation: NavItem[] = isStudent
    ? STUDENT_NAV
    : [
        ...(canSeeAdmin ? [ADMIN_DASHBOARD] : []),
        ...(canSeeCourses ? [ADMIN_CURSOS] : []),
        PERFIL_NAV,
      ]

  const section = ROUTE_SECTIONS[route] ?? 'Plataforma'
  const homeHref = isStudent ? '#/dashboard' : canSeeAdmin ? '#/admin/dashboard' : '#/admin/cursos'
  const userInitials = initials(user.nome_completo || user.email)

  useEffect(() => {
    setNavOpen(false)
  }, [route])

  useEffect(() => {
    if (!navOpen) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setNavOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [navOpen])

  const handleLogout = () => {
    onLogout()
    window.location.hash = '#/entrar'
  }

  return (
    <div className={`app-shell${navOpen ? ' app-shell--nav-open' : ''}`}>
      <aside className="app-sidebar" aria-label="Navegação da plataforma">
        <div className="app-sidebar__brand">
          <BrandMark theme="light" href={homeHref} emblemSize={40} />
          <button
            type="button"
            className="app-sidebar__close"
            onClick={() => setNavOpen(false)}
            aria-label="Fechar menu"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="app-nav">
          <p className="app-nav__label">{isStudent ? 'Aprendizagem' : 'Gestão'}</p>
          {navigation.map(({ href, label, icon: Icon, routes }) => {
            const active = routes.includes(route)
            return (
              <a
                key={href}
                href={href}
                className={`app-nav__link${active ? ' is-active' : ''}`}
                aria-current={active ? 'page' : undefined}
              >
                <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
                <span>{label}</span>
              </a>
            )
          })}
        </nav>

        <div className="app-sidebar__footer">
          <a className="app-sidebar__site" href="#inicio">
            <ExternalLink size={15} aria-hidden="true" />
            Voltar ao site
          </a>
          <div className="app-sidebar__account">
            <span className="app-avatar app-avatar--light" aria-hidden="true">{userInitials}</span>
            <span className="app-sidebar__account-meta">
              <strong>{user.nome_completo || user.email}</strong>
              <small>{roleLabel(user.role)}</small>
            </span>
            <button
              type="button"
              className="app-sidebar__logout"
              onClick={handleLogout}
              aria-label="Terminar sessão"
              title="Terminar sessão"
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>

      {navOpen && (
        <button
          type="button"
          className="app-scrim"
          onClick={() => setNavOpen(false)}
          aria-label="Fechar menu"
          tabIndex={-1}
        />
      )}

      <div className="app-main">
        <header className="app-topbar">
          <button
            type="button"
            className="app-topbar__menu"
            onClick={() => setNavOpen(true)}
            aria-label="Abrir menu"
            aria-expanded={navOpen}
          >
            <Menu size={20} />
          </button>

          <div className="app-topbar__crumb">
            <span>CLOP Academia</span>
            <ChevronRight size={14} aria-hidden="true" />
            <strong>{section}</strong>
          </div>

          <div className="app-topbar__actions">
            {isStudent && (
              <a className="app-icon-btn" href="#/notificacoes" aria-label="Notificações" title="Notificações">
                <Bell size={19} />
              </a>
            )}
            <a className="app-topbar__site" href="#inicio">
              <ExternalLink size={15} aria-hidden="true" />
              <span>Site</span>
            </a>
            <div className="app-user">
              <span className="app-avatar app-avatar--sm" aria-hidden="true">{userInitials}</span>
              <span className="app-user__meta">
                <strong>{user.nome_completo || user.email}</strong>
                <small>{roleLabel(user.role)}</small>
              </span>
            </div>
          </div>
        </header>

        <main className="app-content">{children}</main>

        <footer className="app-footer">
          <span>© {new Date().getFullYear()} CLOP Academia Digital, LDA.</span>
          <span>Educação Financeira &amp; Mercados</span>
        </footer>
      </div>
    </div>
  )
}
