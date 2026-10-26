import { loadEnv } from 'vite'

if (process.env.VERCEL !== '1') process.exit(0)

const { VITE_API_URL } = loadEnv('production', process.cwd(), 'VITE_')
const configuredApiBase = VITE_API_URL?.trim()

if (!configuredApiBase) {
  throw new Error('VITE_API_URL tem de estar configurada para o deploy de produção.')
}

let apiUrl
try {
  apiUrl = new URL(configuredApiBase)
} catch (error) {
  if (error instanceof TypeError) {
    throw new Error('VITE_API_URL não contém um URL válido.')
  }
  throw error
}

if (
  apiUrl.protocol !== 'https:' ||
  ['localhost', '127.0.0.1', '::1'].includes(apiUrl.hostname)
) {
  throw new Error('VITE_API_URL deve apontar para o URL HTTPS público da API em produção.')
}
