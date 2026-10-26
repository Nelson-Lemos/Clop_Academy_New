import { useEffect, useState } from 'react'
import { CheckCircle2, CreditCard, Receipt, Wallet } from 'lucide-react'
import { alunoApi, type PagamentoAluno } from '../../lib/api'
import { PageHeader } from '../../components/PageHeader'
import { EmptyState } from '../../components/EmptyState'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { estadoLabel, estadoTone, formatDate, formatKz } from '../../lib/labels'

export default function Pagamentos() {
  const [pagamentos, setPagamentos] = useState<PagamentoAluno[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    alunoApi
      .getPagamentos()
      .then((data) => {
        if (active) setPagamentos(data)
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar os pagamentos.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [reloadKey])

  const confirmados = pagamentos.filter((p) => p.estado.toUpperCase() === 'CONFIRMADO')
  const pendentes = pagamentos.filter((p) => ['PENDENTE', 'AGUARDA_PAGAMENTO'].includes(p.estado.toUpperCase()))
  const totalConfirmado = confirmados.reduce((total, p) => total + p.valor, 0)
  const totalPendente = pendentes.reduce((total, p) => total + p.valor, 0)

  return (
    <>
      <PageHeader
        eyebrow="Financeiro"
        title="Pagamentos"
        description="Histórico de pagamentos das suas inscrições e respetivo estado de confirmação."
      />

      {loading && <LoadingState label="A carregar pagamentos…" />}
      {!loading && error && <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />}

      {!loading && !error && pagamentos.length === 0 && (
        <EmptyState
          icon={Wallet}
          title="Nenhum pagamento registado"
          description="Quando efetuar uma inscrição com pagamento, o histórico aparecerá nesta área."
        />
      )}

      {!loading && !error && pagamentos.length > 0 && (
        <>
          <section className="summary-strip" aria-label="Resumo financeiro">
            <article className="summary-pill">
              <span className="summary-pill__icon summary-pill__icon--green" aria-hidden="true">
                <CheckCircle2 size={18} />
              </span>
              <div>
                <span>Total confirmado</span>
                <strong>{formatKz(totalConfirmado)}</strong>
              </div>
            </article>
            <article className="summary-pill">
              <span className="summary-pill__icon summary-pill__icon--gold" aria-hidden="true">
                <CreditCard size={18} />
              </span>
              <div>
                <span>Valor pendente</span>
                <strong>{formatKz(totalPendente)}</strong>
              </div>
            </article>
            <article className="summary-pill">
              <span className="summary-pill__icon summary-pill__icon--neutral" aria-hidden="true">
                <Receipt size={18} />
              </span>
              <div>
                <span>Registos</span>
                <strong>{pagamentos.length}</strong>
              </div>
            </article>
          </section>

          <section className="app-card app-card--flush">
            <div className="table-scroll">
              <table className="app-table">
                <thead>
                  <tr>
                    <th scope="col">Referência</th>
                    <th scope="col">Valor</th>
                    <th scope="col">Método</th>
                    <th scope="col">Estado</th>
                    <th scope="col">Criado em</th>
                    <th scope="col">Confirmado em</th>
                  </tr>
                </thead>
                <tbody>
                  {pagamentos.map((pagamento) => (
                    <tr key={pagamento.id}>
                      <td>
                        <strong className="mono">{pagamento.referencia}</strong>
                      </td>
                      <td>
                        <strong>{formatKz(pagamento.valor)}</strong>
                      </td>
                      <td className="app-table__muted">{pagamento.metodo}</td>
                      <td>
                        <span className={`badge badge--${estadoTone(pagamento.estado)}`}>
                          {estadoLabel(pagamento.estado)}
                        </span>
                      </td>
                      <td className="app-table__muted">{formatDate(pagamento.criado_em)}</td>
                      <td className="app-table__muted">{formatDate(pagamento.confirmado_em)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </>
  )
}
