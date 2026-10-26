const API_BASE = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace(
  /\/+$/,
  '',
)

const ACCESS_KEY = 'clop:access'
const REFRESH_KEY = 'clop:refresh'
const USER_KEY = 'clop:user'

export type StudentProfile = {
  profissao: string | null
  empresa: string | null
  cidade: string | null
  provincia: string | null
  nivel_educacao: string | null
  area_interesse: string | null
  objetivo: string | null
  biografia: string | null
  linkedin: string | null
  newsletter_inscrito: boolean
}

export type AuthUser = {
  id: number
  nome_completo: string
  email: string
  telefone: string | null
  role: string
  estado: string
  aceite_termos_em: string | null
  email_verificado_em: string | null
  criado_em: string
  perfil_aluno: StudentProfile | null
  permissoes: string[]
}

export type AuthResponse = {
  access_token: string
  refresh_token: string
  token_type: string
  user: AuthUser
}

export type LoginPayload = {
  email: string
  password: string
}

export type RegisterPayload = {
  nome_completo: string
  email: string
  telefone?: string | null
  password: string
  aceite_termos: boolean
  aceite_privacidade: boolean
  provincia?: string | null
  cidade?: string | null
  objetivo?: string | null
}

export class ApiError extends Error {
  status: number
  details: string[]

  constructor(message: string, status: number, details: string[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

function readDetail(payload: unknown): string[] {
  if (!payload || typeof payload !== 'object') {
    return []
  }

  const detail = (payload as { detail?: unknown }).detail

  if (typeof detail === 'string') {
    return [detail]
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item) {
          const message = (item as { msg?: unknown }).msg
          return typeof message === 'string' ? message : ''
        }
        return ''
      })
      .filter(Boolean)
  }

  return []
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
    })
  } catch {
    throw new ApiError(
      'Não foi possível ligar ao servidor da CLOP. Verifique a ligação e tente novamente.',
      0,
    )
  }

  const payload = (await response.json().catch(() => null)) as unknown

  if (!response.ok) {
    const details = readDetail(payload)
    throw new ApiError(details[0] ?? 'Não foi possível concluir o pedido.', response.status, details)
  }

  return payload as T
}

function storages(): Storage[] {
  return [localStorage, sessionStorage]
}

function clearSession() {
  for (const storage of storages()) {
    storage.removeItem(ACCESS_KEY)
    storage.removeItem(REFRESH_KEY)
    storage.removeItem(USER_KEY)
  }
}

function activeStorage(): Storage | null {
  for (const storage of storages()) {
    if (storage.getItem(ACCESS_KEY)) return storage
  }
  return null
}

function persistSession(response: AuthResponse, remember: boolean) {
  clearSession()
  const storage = remember ? localStorage : sessionStorage
  storage.setItem(ACCESS_KEY, response.access_token)
  storage.setItem(REFRESH_KEY, response.refresh_token)
  storage.setItem(USER_KEY, JSON.stringify(response.user))
}

function accessToken(): string | null {
  for (const storage of storages()) {
    const token = storage.getItem(ACCESS_KEY)
    if (token) return token
  }
  return null
}

function refreshToken(): string | null {
  for (const storage of storages()) {
    const token = storage.getItem(REFRESH_KEY)
    if (token) return token
  }
  return null
}

function cachedUser(): AuthUser | null {
  for (const storage of storages()) {
    const raw = storage.getItem(USER_KEY)
    if (!raw) continue
    try {
      return JSON.parse(raw) as AuthUser
    } catch {
      storage.removeItem(USER_KEY)
    }
  }
  return null
}

async function refreshAccessToken(): Promise<boolean> {
  const token = refreshToken()
  const storage = activeStorage()
  if (!token || !storage) return false

  try {
    const response = await request<{
      access_token: string
      refresh_token: string
      token_type: string
    }>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: token }),
    })
    storage.setItem(ACCESS_KEY, response.access_token)
    storage.setItem(REFRESH_KEY, response.refresh_token)
    return true
  } catch {
    return false
  }
}

async function authenticatedRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = accessToken()
  if (!token) {
    throw new ApiError('Sessão não encontrada.', 401)
  }

  const send = (accessToken: string) => {
    const headers = new Headers(init.headers)
    headers.set('Authorization', `Bearer ${accessToken}`)
    return request<T>(path, {
      ...init,
      headers,
    })
  }

  try {
    return await send(token)
  } catch (error) {
    if (error instanceof ApiError && error.status === 401 && (await refreshAccessToken())) {
      const renewed = accessToken()
      if (renewed) return send(renewed)
    }
    throw error
  }
}

async function me(): Promise<AuthUser> {
  const token = accessToken()
  if (!token) {
    throw new ApiError('Sessão não encontrada.', 401)
  }

  try {
    const user = await request<AuthUser>('/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
    const storage = activeStorage()
    storage?.setItem(USER_KEY, JSON.stringify(user))
    return user
  } catch (error) {
    if (error instanceof ApiError && error.status === 401 && (await refreshAccessToken())) {
      const renewed = accessToken()
      if (!renewed) throw error
      const user = await request<AuthUser>('/auth/me', {
        headers: { Authorization: `Bearer ${renewed}` },
      })
      activeStorage()?.setItem(USER_KEY, JSON.stringify(user))
      return user
    }
    throw error
  }
}

export const authApi = {
  baseUrl: API_BASE,
  login: async (payload: LoginPayload, remember = true) => {
    const response = await request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    persistSession(response, remember)
    return response
  },
  register: async (payload: RegisterPayload, remember = true) => {
    const response = await request<AuthResponse>('/auth/registo', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    persistSession(response, remember)
    return response
  },
  me,
  logout: clearSession,
  hasSession: () => Boolean(accessToken()),
  cachedUser,
  clearSession,
}

// ============================================================================
// Tipos públicos
// ============================================================================

export type CursoPublico = {
  id: number
  nome: string
  slug: string
  resumo: string | null
  imagem_url: string | null
  modalidade: string
  duracao_horas: number
  preco: number | null
  estado: string
  categoria_nome: string | null
}

export type ArtigoPublico = {
  id: number
  titulo: string
  slug: string
  resumo: string | null
  imagem_url: string | null
  tipo: string
  categoria_nome: string | null
  autor_nome: string | null
  publicado_em: string | null
  leitura_minutos: number
}

export type EventoPublico = {
  id: number
  titulo: string
  slug: string
  resumo: string | null
  imagem_url: string | null
  local: string | null
  cidade: string | null
  inicio: string | null
  fim: string | null
  formato: string | null
  vagas: number | null
  inscricoes_abertas: boolean
  requer_inscricao: boolean
  estado: string
}

export type ProjectoPublico = {
  id: number
  titulo: string
  slug: string | null
  resumo: string | null
  imagem_url: string | null
  estado: string
}

export type CampanhaPublica = {
  id: number
  titulo: string
  descricao: string | null
  imagem_url: string | null
  estado: string
}

export type MercadosView = {
  instrumentos: Array<{
    simbolo: string
    nome: string
    preco: number | null
    variacao: number | null
    fonte: string | null
    frescura: string | null
  }>
  fontes: Array<{
    nome: string
    estado: string
    ultimo_sync: string | null
  }>
}

// ============================================================================
// Tipos da área do aluno
// ============================================================================

export type InscricaoAluno = {
  id: number
  course_id: number
  cohort_id: number | null
  estado: string
  preco_pago: number
  termos_aceites: boolean
  percentagem_progresso: number
  iniciado_em: string | null
  concluido_em: string | null
  criado_em: string
  curso_nome: string
  curso_slug: string
  curso_imagem: string | null
  curso_modalidade: string
  curso_duracao_horas: number
  total_aulas: number
  aulas_concluidas: number
  proxima_aula: string | null
  proxima_aula_id: number | null
  avaliacoes_pendentes: number
  certificado_disponivel: boolean
}

export type DashboardAluno = {
  metricas: {
    total_inscricoes: number
    inscricoes_ativas: number
    inscricoes_concluidas: number
    progresso_medio: number
    proximos_eventos: number
  }
  notificacoes_nao_lidas: number
  cursos: InscricaoAluno[]
  proximas_aulas: Array<{
    curso_id: number
    curso_nome: string
    aula_id: number
    aula_titulo: string
    duracao_minutos: number
    tipo: string
  }>
}

export type ModuloCurso = {
  id: number
  titulo: string
  descricao: string | null
  ordem: number
  aulas: AulaCurso[]
}

export type AulaCurso = {
  id: number
  titulo: string
  descricao: string | null
  tipo: string
  ordem: number
  duracao_minutos: number
  video_url: string | null
  link_live: string | null
  data_live: string | null
  obrigatoria: boolean
  conteudo: string | null
  materiais: Array<{
    id: number
    titulo: string
    descricao: string | null
    tipo: string
    url: string | null
  }>
  concluida: boolean
  percentagem_video: number
  ultima_posicao_segundos: number
}

export type ConteudoCurso = {
  curso: {
    id: number
    nome: string
    slug: string
    modalidade: string
    duracao_horas: number
    percentagem_conclusao_minima: number
  }
  inscricao: {
    id: number
    estado: string
    percentagem_progresso: number
    iniciado_em: string | null
    concluido_em: string | null
  }
  modulos: ModuloCurso[]
}

export type DetalheAula = {
  id: number
  titulo: string
  descricao: string | null
  tipo: string
  duracao_minutos: number
  conteudo: string | null
  video_url: string | null
  link_live: string | null
  data_live: string | null
  obrigatoria: boolean
  materiais: Array<{
    id: number
    titulo: string
    descricao: string | null
    tipo: string
    url: string | null
  }>
  concluida: boolean
  percentagem_video: number
  ultima_posicao_segundos: number
}

export type AvaliacaoAluno = {
  id: number
  course_id: number
  titulo: string
  descricao: string | null
  tipo: string
  nota_maxima: number
  nota_aprovacao: number
  tempo_limite_minutos: number | null
  tentativas_maximas: number
  disponivel_de: string | null
  disponivel_ate: string | null
  total_perguntas: number
  tentativas_usadas: number
  ultima_nota: number | null
  ultima_submissao: string | null
  corrigida: boolean
  feedback: string | null
  perguntas?: Array<{
    id: number
    enunciado: string
    tipo: string
    opcoes: string | null
    pontos: number
    ordem: number
  }>
}

export type SubmissaoAvaliacao = {
  assessment_id: number
  respostas: Record<string, string>
}

export type PagamentoAluno = {
  id: number
  enrollment_id: number
  curso_id: number
  referencia: string
  valor: number
  moeda: string
  metodo: string
  estado: string
  provider: string | null
  provider_reference: string | null
  notas: string | null
  confirmado_em: string | null
  criado_em: string
}

export type CertificadoAluno = {
  id: number
  codigo: string
  curso_id: number
  enrollment_id: number
  estado: string
  nota_final: number | null
  emitido_em: string
  curso_nome: string | null
  aluno_nome: string | null
}

export type NotificacaoAluno = {
  id: number
  titulo: string
  mensagem: string
  tipo: string
  ligacao: string | null
  lida: boolean
  criado_em: string
}

// ============================================================================
// Tipos de administração
// ============================================================================

export type DashboardAdmin = {
  alunos_registados: number
  inscricoes_por_curso: Array<{ curso_id: number; curso: string; total: number }>
  cursos_activos: number
  cursos_publicados: number
  pagamentos_pendentes: number
  pagamentos_confirmados: number
  total_inscricoes: number
  inscricoes_activas: number
  artigos_publicados: number
  eventos_publicados: number
  eventos_proximos: number
  pedidos_contacto: number
  certificados_emitidos: number
  avaliacoes_pendentes: number
}

// ============================================================================
// APIs públicas
// ============================================================================

export const publicApi = {
  getInstituicao: async () => {
    return request<any>('/public/instituicao')
  },
  getHome: async () => {
    return request<any>('/public/home')
  },
  getCursos: async (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return request<CursoPublico[]>('/public/cursos' + qs)
  },
  getCursoDetalhe: async (slug: string) => {
    return request<any>('/public/cursos/' + encodeURIComponent(slug))
  },
  getArtigos: async () => {
    return request<ArtigoPublico[]>('/public/artigos')
  },
  getEventos: async () => {
    return request<EventoPublico[]>('/public/eventos')
  },
  getProjectos: async () => {
    return request<ProjectoPublico[]>('/public/projectos')
  },
  getCampanhas: async () => {
    return request<CampanhaPublica[]>('/public/campanhas')
  },
  getMercados: async () => {
    return request<MercadosView>('/public/mercados')
  },
  postContacto: async (payload: any) => {
    return request<{ mensagem: string }>('/public/contactos', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  postNewsletter: async (payload: any) => {
    return request<{ mensagem: string }>('/public/newsletter', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}

// ============================================================================
// API da área do aluno
// ============================================================================

export const alunoApi = {
  getDashboard: async () => {
    return authenticatedRequest<DashboardAluno>('/aluno/dashboard')
  },
  getInscricoes: async () => {
    return authenticatedRequest<InscricaoAluno[]>('/aluno/inscricoes')
  },
  postInscricao: async (payload: { course_id: number; cohort_id?: number; aceite_termos: boolean }) => {
    return authenticatedRequest<any>('/aluno/inscricoes', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  cancelarInscricao: async (inscricaoId: number) => {
    return authenticatedRequest<{ mensagem: string }>('/aluno/inscricoes/' + inscricaoId + '/cancelar', {
      method: 'POST',
    })
  },
  getConteudoCurso: async (courseId: number) => {
    return authenticatedRequest<ConteudoCurso>('/aluno/cursos/' + courseId + '/conteudo')
  },
  getDetalheAula: async (courseId: number, lessonId: number) => {
    return authenticatedRequest<DetalheAula>('/aluno/cursos/' + courseId + '/aulas/' + lessonId)
  },
  postProgresso: async (courseId: number, payload: { lesson_id: number; concluida?: boolean; percentagem_video?: number; ultima_posicao_segundos?: number }) => {
    return authenticatedRequest<any>('/aluno/cursos/' + courseId + '/progresso', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  getAvaliacoes: async () => {
    return authenticatedRequest<AvaliacaoAluno[]>('/aluno/avaliacoes')
  },
  getDetalheAvaliacao: async (assessmentId: number) => {
    return authenticatedRequest<AvaliacaoAluno>('/aluno/avaliacoes/' + assessmentId)
  },
  postSubmissaoAvaliacao: async (payload: SubmissaoAvaliacao) => {
    return authenticatedRequest<any>('/aluno/avaliacoes/submissao', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  getPagamentos: async () => {
    return authenticatedRequest<PagamentoAluno[]>('/aluno/pagamentos')
  },
  getCertificados: async () => {
    return authenticatedRequest<CertificadoAluno[]>('/aluno/certificados')
  },
  postEmitirCertificado: async (inscricaoId: number) => {
    return authenticatedRequest<CertificadoAluno>('/aluno/certificados/' + inscricaoId + '/emitir', {
      method: 'POST',
    })
  },
  getNotificacoes: async (apenasNaoLidas = false) => {
    const qs = apenasNaoLidas ? '?apenas_nao_lidas=true' : ''
    return authenticatedRequest<NotificacaoAluno[]>('/aluno/notificacoes' + qs)
  },
  postMarcarNotificacaoLida: async (notificationId: number) => {
    return authenticatedRequest<{ ok: boolean }>('/aluno/notificacoes/' + notificationId + '/ler', {
      method: 'POST',
    })
  },
  postMarcarTodasLidas: async () => {
    return authenticatedRequest<{ ok: boolean; actualizadas: number }>('/aluno/notificacoes/ler-todas', {
      method: 'POST',
    })
  },
  postAlterarEstadoInscricao: async (inscricaoId: number, estado: string, motivo?: string) => {
    return authenticatedRequest<any>('/aluno/inscricoes/' + inscricaoId + '/estado', {
      method: 'POST',
      body: JSON.stringify({ estado, motivo }),
    })
  },
}

// ============================================================================
// API de administração
// ============================================================================

export const adminApi = {
  getDashboard: async () => {
    return authenticatedRequest<DashboardAdmin>('/admin/dashboard')
  },
  getCursos: async () => {
    return authenticatedRequest<any[]>('/admin/cursos')
  },
}
