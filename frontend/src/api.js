const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL || 'https://ipms-roles-recommeder.onrender.com').replace(/\/$/, '')

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`
  console.log('API request:', url)

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || 'Request failed')
  }

  return response.json()
}

export function fetchBootstrap() {
  return request('/api/bootstrap')
}

export function fetchVerticals(level) {
  return request(`/api/verticals?level=${encodeURIComponent(level)}`)
}

export function fetchRecommendations(payload) {
  return request('/api/recommendations', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

const VISITOR_ID_KEY = 'ipms_visitor_id'
const SESSION_ID_KEY = 'ipms_session_id'

function createTrackingId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID()
  }
  return `${Date.now()}_${Math.random().toString(16).slice(2)}`
}

export function getOrCreateVisitorId() {
  let visitorId = localStorage.getItem(VISITOR_ID_KEY)
  if (!visitorId) {
    visitorId = createTrackingId()
    localStorage.setItem(VISITOR_ID_KEY, visitorId)
  }
  return visitorId
}

export function getOrCreateSessionId() {
  let sessionId = sessionStorage.getItem(SESSION_ID_KEY)
  if (!sessionId) {
    sessionId = createTrackingId()
    sessionStorage.setItem(SESSION_ID_KEY, sessionId)
  }
  return sessionId
}

export function trackUsageSnapshot(payload) {
  return request('/api/tracking/snapshot', {
    method: 'POST',
    body: JSON.stringify({
      visitor_id: getOrCreateVisitorId(),
      session_id: getOrCreateSessionId(),
      ...payload,
    }),
  })
}

export function trackUsageSnapshotBeacon(payload) {
  const url = `${API_BASE_URL}/api/tracking/snapshot`
  const body = JSON.stringify({
    visitor_id: getOrCreateVisitorId(),
    session_id: getOrCreateSessionId(),
    ...payload,
  })

  if (navigator.sendBeacon) {
    const blob = new Blob([body], { type: 'application/json' })
    navigator.sendBeacon(url, blob)
    return
  }

  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    keepalive: true,
  }).catch(() => {})
}