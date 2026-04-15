const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://ipms-roles-recommeder.onrender.com/'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
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
