import { AlertCircle, RotateCcw } from 'lucide-react'

type ErrorStateProps = {
  message: string
  onRetry?: () => void
}

/** Bloco de erro com acção de nova tentativa. */
export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="error-state" role="alert">
      <span className="error-state__icon" aria-hidden="true">
        <AlertCircle size={22} />
      </span>
      <div className="error-state__text">
        <strong>Não foi possível carregar</strong>
        <p>{message}</p>
      </div>
      {onRetry && (
        <button type="button" className="btn btn--outline btn--sm" onClick={onRetry}>
          <RotateCcw size={14} aria-hidden="true" />
          Tentar novamente
        </button>
      )}
    </div>
  )
}
