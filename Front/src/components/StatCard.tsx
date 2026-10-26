import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

type StatCardProps = {
  icon: LucideIcon
  label: string
  value: ReactNode
  hint?: string
  tone?: 'gold' | 'green' | 'blue' | 'red' | 'neutral'
}

/** Cartão de indicador (KPI) usado nos dashboards. */
export function StatCard({ icon: Icon, label, value, hint, tone = 'gold' }: StatCardProps) {
  return (
    <article className={`stat-card stat-card--${tone}`}>
      <span className="stat-card__icon" aria-hidden="true">
        <Icon size={19} strokeWidth={1.8} />
      </span>
      <div className="stat-card__body">
        <p className="stat-card__label">{label}</p>
        <p className="stat-card__value">{value}</p>
        {hint && <p className="stat-card__hint">{hint}</p>}
      </div>
    </article>
  )
}
