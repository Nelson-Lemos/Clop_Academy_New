type LoadingStateProps = {
  label?: string
}

/** Indicador de carregamento acessível. */
export function LoadingState({ label = 'A carregar…' }: LoadingStateProps) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}

/** Esqueleto de dashboard apresentado durante o primeiro carregamento. */
export function DashboardSkeleton() {
  return (
    <div className="skeleton-page" aria-hidden="true">
      <div className="skeleton skeleton--hero" />
      <div className="skeleton-grid">
        {[0, 1, 2, 3].map((item) => (
          <div key={item} className="skeleton skeleton--stat" />
        ))}
      </div>
      <div className="skeleton-grid skeleton-grid--wide">
        <div className="skeleton skeleton--panel" />
        <div className="skeleton skeleton--panel" />
      </div>
    </div>
  )
}
