// Simple API client for backend (6060) and internal API (5050)
// Unified token source: prefers 'supabase_token' then falls back to 'apiToken'.

const DEFAULTS = {
  backendBase: 'http://127.0.0.1:6060',
  internalBase: 'http://127.0.0.1:5050',
};

function authHeaders() {
  const supa = (typeof localStorage !== 'undefined' && localStorage.getItem('supabase_token')) || ''
  const apiT = (typeof localStorage !== 'undefined' && localStorage.getItem('apiToken')) || ''
  const t = supa || apiT
  const h = { 'Content-Type': 'application/json' }
  const requireAuth = String(import.meta?.env?.VITE_REQUIRE_AUTH ?? 'true').toLowerCase() !== 'false'
  if (t && requireAuth) h['Authorization'] = 'Bearer ' + t
  return h
}

export function activeTokenSource() {
  try {
    const supa = localStorage.getItem('supabase_token') || ''
    const apiT = localStorage.getItem('apiToken') || ''
    if (supa) return 'supabase'
    if (apiT) return 'dev'
    return 'none'
  } catch { return 'none' }
}

export function isAuthRequired() {
  try { return String(import.meta?.env?.VITE_REQUIRE_AUTH ?? 'true').toLowerCase() !== 'false' } catch { return true }
}

export const api = {
  setToken(token) {
    try { localStorage.setItem('apiToken', token || '') } catch {}
  },
  getToken() {
    try { return localStorage.getItem('apiToken') || '' } catch { return '' }
  },
  async getConfig(base = DEFAULTS.backendBase) {
    const res = await fetch(base + '/config/', { headers: authHeaders() })
    const json = await res.json().catch(() => ({}))
    return { ok: res.ok, json, validated: res.headers.get('X-Response-Validated') }
  },
  async setConfig(payload, base = DEFAULTS.backendBase) {
    const res = await fetch(base + '/config/', { method: 'POST', headers: authHeaders(), body: JSON.stringify(payload || {}) })
    const json = await res.json().catch(() => ({}))
    return { ok: res.ok, json, validated: res.headers.get('X-Response-Validated') }
  },
  async getAuthStatus(base = DEFAULTS.backendBase) {
    const res = await fetch(base + '/auth/status', { headers: authHeaders() })
    const json = await res.json().catch(() => ({}))
    return { ok: res.ok, json }
  },
  async reloadConfig(base = DEFAULTS.backendBase) {
    const res = await fetch(base + '/config/reload', { method: 'POST', headers: authHeaders() })
    const json = await res.json().catch(() => ({}))
    return { ok: res.ok, json, validated: res.headers.get('X-Response-Validated') }
  },
  async memoryStore(prompt, response, base = DEFAULTS.backendBase) {
    const res = await fetch(base + '/memory/store', { method: 'POST', headers: authHeaders(), body: JSON.stringify({ prompt, response }) })
    const json = await res.json().catch(() => ({}))
    return { ok: res.ok, json, validated: res.headers.get('X-Response-Validated') }
  },
  async memoryQuery(q, limit = 50, base = DEFAULTS.backendBase) {
    const res = await fetch(base + '/memory/query', { method: 'POST', headers: authHeaders(), body: JSON.stringify({ q, limit }) })
    const json = await res.json().catch(() => ({}))
    return { ok: res.ok, json, validated: res.headers.get('X-Response-Validated') }
  },
  async voiceCommand(text, base = DEFAULTS.backendBase) {
    const res = await fetch(base + '/voice/command', { method: 'POST', headers: authHeaders(), body: JSON.stringify({ text }) })
    const json = await res.json().catch(() => ({}))
    return { ok: res.ok, json, validated: res.headers.get('X-Response-Validated') }
  },
  async updatesApply(base = DEFAULTS.backendBase) {
    const res = await fetch(base + '/updates/apply', { method: 'POST', headers: authHeaders() })
    const json = await res.json().catch(() => ({}))
    return { ok: res.ok, json, validated: res.headers.get('X-Response-Validated') }
  },
}