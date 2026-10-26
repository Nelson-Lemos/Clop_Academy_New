import { useEffect, useMemo, useState } from 'react'
import { Bell, BellRing, CheckCheck } from 'lucide-react'
import { alunoApi, type NotificacaoAluno } from '../../lib/api'
import { PageHeader } from '../../components/PageHeader'
import { EmptyState } from '../../components/EmptyState'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { formatDateTime } from '../../lib/labels'

type Filtro = 'todas' | 'nao-lidas'

export default function Notificacoes() {
  const [notificacoes, setNotificacoes] = useState<NotificacaoAluno[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)
  const [filtro, setFiltro] = useState<Filtro>('todas')
  const [aProcessar, setAProcessar] = useState(false)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    alunoApi
      .getNotificacoes()
      .then((data) => {
        if (active) setNotificacoes(data)
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar as notificações.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadKey])

  const naoLidas = notificacoes.filter((notificacao) => !notificacao.lida).length

  const visiveis = useMemo(
    () => (filtro === 'nao-lidas' ? notificacoes.filter((notificacao) => !notificacao.lida) : notificacoes),
    [notificacoes, filtro],
  )

  const marcarLida = async (id: number) => {
    try {
      await alunoApi.postMarcarNotificacaoLida(id)
      setNotificacoes((prev) => prev.map((n) => (n.id === id ? { ...n, lida: true } : n)))
    } catch {
      setError('Não foi possível marcar a notificação como lida.')
    }
  }

  const marcarTodas = async () => {
    if (aProcessar) return
    setAProcessar(true)
    try {
      await alunoApi.postMarcarTodasLidas()
      setNotificacoes((prev) => prev.map((n) => ({ ...n, lida: true })))
    } catch {
      setError('Não foi possível marcar as notificações como lidas.')
    } finally {
      setAProcessar(false)
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Comunicações"
        title="Notificações"
        description={
          naoLidas > 0
            ? `Tem ${naoLidas} notificação(ões) por ler.`
            : 'Está a par de todas as novidades da plataforma.'
        }
        actions={
          <button
            type="button"
            className="btn btn--ghost btn--sm"
            onClick={marcarTodas}
            disabled={aProcessar || naoLidas === 0}
          >
            <CheckCheck size={15} aria-hidden="true" />
            Marcar todas como lidas
          </button>
        }
      />

      {loading && <LoadingState label="A carregar notificações…" />}
      {!loading && error && <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />}

      {!loading && !error && (
        <>
          <div className="toolbar toolbar--plain">
            <div className="toolbar__filters" role="group" aria-label="Filtrar notificações">
              <button
                type="button"
                className={`filter-chip${filtro === 'todas' ? ' is-active' : ''}`}
                aria-pressed={filtro === 'todas'}
                onClick={() => setFiltro('todas')}
              >
                Todas
                <span className="filter-chip__count">{notificacoes.length}</span>
              </button>
              <button
                type="button"
                className={`filter-chip${filtro === 'nao-lidas' ? ' is-active' : ''}`}
                aria-pressed={filtro === 'nao-lidas'}
                onClick={() => setFiltro('nao-lidas')}
              >
                Não lidas
                <span className="filter-chip__count">{naoLidas}</span>
              </button>
            </div>
          </div>

          {visiveis.length === 0 ? (
            <EmptyState
              icon={Bell}
              title={filtro === 'nao-lidas' ? 'Sem notificações por ler' : 'Sem notificações'}
              description="Novas comunicações sobre cursos, avaliações e pagamentos aparecerão aqui."
            />
          ) : (
            <ul className="notification-list">
              {visiveis.map((notificacao) => (
                <li
                  key={notificacao.id}
                  className={`notification-item${notificacao.lida ? '' : ' is-unread'}`}
                >
                  <span className="notification-item__icon" aria-hidden="true">
                    {notificacao.lida ? <Bell size={18} /> : <BellRing size={18} />}
                  </span>
                  <div className="notification-item__body">
                    <div className="notification-item__head">
                      <strong>{notificacao.titulo}</strong>
                      <span className="notification-item__date">
                        {formatDateTime(notificacao.criado_em)}
                      </span>
                    </div>
                    <p>{notificacao.mensagem}</p>
                    {notificacao.ligacao && (
                      <a className="app-link app-link--sm" href={notificacao.ligacao}>
                        Abrir
                      </a>
                    )}
                  </div>
                  {!notificacao.lida && (
                    <button
                      type="button"
                      className="btn btn--ghost btn--sm"
                      onClick={() => marcarLida(notificacao.id)}
                    >
                      Marcar como lida
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </>
  )
}
