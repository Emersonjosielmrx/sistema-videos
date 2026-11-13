const API = '/api'

function getToken(): string | null {
  return localStorage.getItem('fluxia_token')
}

export function setToken(token: string) {
  localStorage.setItem('fluxia_token', token)
}

export function clearToken() {
  localStorage.removeItem('fluxia_token')
  localStorage.removeItem('fluxia_role')
}

export function isLoggedIn(): boolean {
  return !!getToken()
}

export function setRole(role: string) {
  localStorage.setItem('fluxia_role', role)
}

export function getRole(): string {
  return localStorage.getItem('fluxia_role') || 'admin'
}

async function request(method: string, path: string, body?: unknown) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const resp = await fetch(`${API}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (resp.status === 401 && token) {
    clearToken()
    window.location.href = '/login'
    throw new Error('Sessão expirada')
  }
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err.detail || err.message || `Erro ${resp.status}`)
  }
  return resp.json()
}

async function blobUrl(path: string): Promise<string> {
  const token = getToken()
  const resp = await fetch(`${API}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!resp.ok) throw new Error(`Erro ${resp.status}`)
  return URL.createObjectURL(await resp.blob())
}

export const api = {
  get: (path: string) => request('GET', path),
  post: (path: string, body?: unknown) => request('POST', path, body),
  put: (path: string, body?: unknown) => request('PUT', path, body),
  delete: (path: string) => request('DELETE', path),
  blobUrl,
}
