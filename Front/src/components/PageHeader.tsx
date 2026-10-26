import type { ReactNode } from 'react'

type PageHeaderProps = {
  eyebrow?: string
  title: string
  description?: string
  actions?: ReactNode
}

/** Cabeçalho de página consistente em todos os módulos autenticados. */
export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <header className="app-page-header">
      <div className="app-page-header__text">
        {eyebrow && <p className="app-page-header__eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p className="app-page-header__desc">{description}</p>}
      </div>
      {actions && <div className="app-page-header__actions">{actions}</div>}
    </header>
  )
}
