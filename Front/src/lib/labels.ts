/**
 * Utilitários de apresentação partilhados pela plataforma autenticada.
 * Centraliza traduções de estados, funções e formatação de datas/valores.
 */

const ROLE_LABELS: Record<string, string> = {
  STUDENT: 'Aluno',
  INSTRUCTOR: 'Formador',
  EDITOR: 'Editor',
  FINANCE: 'Financeiro',
  ADMIN: 'Administrador',
  SUPERADMIN: 'Super Administrador',
}

const ESTADO_LABELS: Record<string, string> = {
  ACTIVA: 'Ativa',
  ATIVA: 'Ativa',
  ACTIVE: 'Ativa',
  INACTIVE: 'Inativa',
  SUSPENDED: 'Suspensa',
  PENDENTE: 'Pendente',
  AGUARDA_PAGAMENTO: 'Aguarda pagamento',
  CONFIRMADO: 'Confirmado',
  CONFIRMADA: 'Confirmada',
  RECUSADO: 'Recusado',
  REEMBOLSADO: 'Reembolsado',
  CONCLUIDA: 'Concluída',
  CONCLUIDO: 'Concluído',
  CANCELADA: 'Cancelada',
  CANCELADO: 'Cancelado',
  EM_CURSO: 'Em curso',
  PUBLICADO: 'Publicado',
  RASCUNHO: 'Rascunho',
  ARQUIVADO: 'Arquivado',
  PLANEADO: 'Planeado',
  EMITIDO: 'Emitido',
  REVOGADO: 'Revogado',
  EXPIRADO: 'Expirado',
}

export function roleLabel(role?: string | null): string {
  if (!role) return 'Aluno'
  return ROLE_LABELS[role.toUpperCase()] ?? role
}

export function estadoLabel(estado?: string | null): string {
  if (!estado) return '—'
  const key = estado.toUpperCase()
  if (ESTADO_LABELS[key]) return ESTADO_LABELS[key]
  const normalized = estado.replace(/_/g, ' ').toLowerCase()
  return normalized.charAt(0).toUpperCase() + normalized.slice(1)
}

export type Tone = 'success' | 'warning' | 'danger' | 'neutral' | 'info'

const SUCCESS = ['ACTIVA', 'ATIVA', 'ACTIVE', 'CONFIRMADO', 'CONFIRMADA', 'PUBLICADO', 'EMITIDO', 'CONCLUIDA', 'CONCLUIDO', 'EM_CURSO']
const WARNING = ['PENDENTE', 'AGUARDA_PAGAMENTO', 'RASCUNHO', 'PLANEADO']
const DANGER = ['CANCELADA', 'CANCELADO', 'RECUSADO', 'REVOGADO', 'SUSPENDED', 'INACTIVE', 'EXPIRADO']

export function estadoTone(estado?: string | null): Tone {
  const key = (estado ?? '').toUpperCase()
  if (SUCCESS.includes(key)) return 'success'
  if (WARNING.includes(key)) return 'warning'
  if (DANGER.includes(key)) return 'danger'
  return 'neutral'
}

export function initials(name?: string | null): string {
  if (!name) return 'CL'
  const parts = name.trim().split(/\s+/).filter(Boolean).slice(0, 2)
  const value = parts.map((part) => part.charAt(0).toUpperCase()).join('')
  return value || 'CL'
}

export function firstName(name?: string | null): string {
  return name?.trim().split(/\s+/)[0] ?? ''
}

export function greeting(date = new Date()): string {
  const hour = date.getHours()
  if (hour < 12) return 'Bom dia'
  if (hour < 19) return 'Boa tarde'
  return 'Boa noite'
}

function parseDate(value?: string | null): Date | null {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDate(value?: string | null): string {
  const date = parseDate(value)
  if (!date) return '—'
  return date.toLocaleDateString('pt-PT', { day: '2-digit', month: 'short', year: 'numeric' })
}

export function formatDateTime(value?: string | null): string {
  const date = parseDate(value)
  if (!date) return '—'
  return date.toLocaleString('pt-PT', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatKz(value?: number | null): string {
  if (value == null) return '—'
  try {
    return new Intl.NumberFormat('pt-AO', {
      style: 'currency',
      currency: 'AOA',
      maximumFractionDigits: 0,
    }).format(value)
  } catch {
    return `${value} Kz`
  }
}

export function todayLabel(date = new Date()): string {
  return date.toLocaleDateString('pt-PT', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
  })
}
