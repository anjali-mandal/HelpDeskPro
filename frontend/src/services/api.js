const API_BASE = import.meta.env.VITE_API_URL || '/api'

async function request(path, options = {}) {
  const token = localStorage.getItem('helpdesk_token')
  const headers = { ...(options.headers || {}) }
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = Array.isArray(payload.detail)
      ? payload.detail.map((item) => item.msg).join(', ')
      : payload.detail
    throw new Error(detail || `Request failed (${response.status})`)
  }
  return payload
}

export const api = {
  login: (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  me: () => request('/users/me'),
  engineers: () => request('/users/engineers'),
  users: () => request('/users'),
  updateUserRole: (id, role) => request(`/users/${id}/role`, { method: 'PATCH', body: JSON.stringify({ role }) }),
  tickets: (status = '') => request(`/tickets${status ? `?status=${status}` : ''}`),
  createTicket: (data) => request('/tickets', { method: 'POST', body: JSON.stringify(data) }),
  updateTicket: (id, data) => request(`/tickets/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  assignTicket: (id, engineer_id) => request(`/tickets/${id}/assign`, { method: 'POST', body: JSON.stringify({ engineer_id }) }),
  comments: (id) => request(`/tickets/${id}/comments`),
  addComment: (id, message) => request(`/tickets/${id}/comments`, { method: 'POST', body: JSON.stringify({ message }) }),
  history: (id) => request(`/tickets/${id}/history`),
  attachments: (id) => request(`/tickets/${id}/attachments`),
  uploadAttachment: (id, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request(`/tickets/${id}/attachments`, { method: 'POST', body: formData })
  },
  downloadAttachment: async (id) => {
    const token = localStorage.getItem('helpdesk_token')
    const response = await fetch(`${API_BASE}/tickets/attachments/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
    if (!response.ok) throw new Error('Unable to download attachment')
    return response.blob()
  },
  notifications: () => request('/notifications?unread_only=false'),
  readNotification: (id) => request(`/notifications/${id}/read`, { method: 'PATCH' }),
  suggestTicket: (data) => request('/ai/suggest', { method: 'POST', body: JSON.stringify(data) }),
  analytics: () => request('/analytics/overview')
}

export function openRealtimeConnection(onEvent) {
  const token = localStorage.getItem('helpdesk_token')
  if (!token) return null
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const socket = new WebSocket(`${protocol}//${window.location.host}/ws?token=${encodeURIComponent(token)}`)
  socket.onmessage = (event) => onEvent(JSON.parse(event.data))
  return socket
}
