// Unified API client using axios (loaded via ESM CDN to avoid local install issues)
// Exports: getConfig, setConfig, getStatus, getLogs

const API_BASE = (import.meta as any)?.env?.VITE_API_URL || 'http://127.0.0.1:6060'
const REQUIRE_AUTH = ((import.meta as any)?.env?.VITE_REQUIRE_AUTH === 'true')

let clientPromise: Promise<any> | null = null

function getToken() {
  try {
    return localStorage.getItem('apiToken') || localStorage.getItem('supabase_token') || ''
  } catch { return '' }
}

function ensureClient() {
  if (!clientPromise) {
    clientPromise = import('https://esm.sh/axios@1.7.7?dev').then((mod: any) => {
      const axios = mod?.default || mod
      const client = axios.create({ baseURL: API_BASE, headers: { 'Content-Type': 'application/json' } })
      client.interceptors.request.use((config: any) => {
        const t = getToken()
        if (REQUIRE_AUTH && t) config.headers = { ...(config.headers || {}), Authorization: `Bearer ${t}` }
        return config
      })
      return client
    })
  }
  return clientPromise
}

export async function getConfig() {
  const client = await ensureClient()
  const res = await client.get('/config/')
  return res.data
}

export async function setConfig(payload: any) {
  const client = await ensureClient()
  const res = await client.post('/config/', payload || {})
  return res.data
}

export async function getStatus() {
  const client = await ensureClient()
  const res = await client.get('/status/')
  return res.data
}

export async function getLogs() {
  const client = await ensureClient()
  const res = await client.get('/logs')
  return res.data
}