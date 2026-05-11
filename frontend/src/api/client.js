const BASE_URL = '/api'

function getToken() {
  return localStorage.getItem('token')
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = { ...options.headers }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(options.body)
  }
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  if (res.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    window.location.href = '/login'
    throw new Error('未登录')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(err.detail || '请求失败')
  }
  return res
}

export async function register(username, password) {
  const res = await request('/auth/register', {
    method: 'POST',
    body: { username, password },
  })
  return res.json()
}

export async function login(username, password) {
  const res = await request('/auth/login', {
    method: 'POST',
    body: { username, password },
  })
  return res.json()
}

export async function generateGame(prompt, onChunk) {
  const token = getToken()
  const res = await fetch(`${BASE_URL}/generate-game`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ prompt }),
  })
  if (res.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    window.location.href = '/login'
    throw new Error('未登录')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '生成失败' }))
    throw new Error(err.detail || '生成失败')
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    onChunk(decoder.decode(value, { stream: true }))
  }
}

export async function getHistory() {
  const res = await request('/history')
  return res.json()
}

export async function clearChat() {
  const res = await request('/clear', { method: 'POST' })
  return res.json()
}

export async function getMemories() {
  const res = await request('/memories/names')
  return res.json()
}

export async function searchMemories(query) {
  const res = await request(`/memories/search?q=${encodeURIComponent(query)}`)
  return res.json()
}
