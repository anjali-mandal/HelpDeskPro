import { useEffect, useState } from 'react'
import TicketDetail from '../components/TicketDetail'
import TicketForm from '../components/TicketForm'
import { useTickets } from '../hooks/useTickets'
import { api, openRealtimeConnection } from '../services/api'

export default function DashboardPage({ user, onLogout }) {
  const [selected, setSelected] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [status, setStatus] = useState('')
  const { tickets, notifications, engineers, error, reload } = useTickets(status, user.role)
  const [analytics, setAnalytics] = useState(null)
  const [adminUsers, setAdminUsers] = useState([])

  useEffect(() => {
    const socket = openRealtimeConnection(() => reload())
    return () => socket?.close()
  }, [reload])

  useEffect(() => {
    if (['manager', 'admin'].includes(user.role)) api.analytics().then(setAnalytics).catch(() => {})
  }, [user.role, tickets.length])

  useEffect(() => {
    if (user.role === 'admin') api.users().then(setAdminUsers).catch(() => {})
  }, [user.role])

  const unreadCount = notifications.filter((n) => !n.is_read).length
  const open = tickets.filter((t) => !['resolved', 'closed'].includes(t.status)).length
  const resolved = tickets.filter((t) => t.status === 'resolved').length
  const urgent = tickets.filter((t) => ['high', 'critical'].includes(t.priority)).length
  const overdue = tickets.filter((t) => (
    t.sla_deadline && !['resolved', 'closed'].includes(t.status) && new Date(t.sla_deadline) < new Date()
  )).length
  const atRisk = tickets.filter((t) => {
    if (!t.sla_deadline || ['resolved', 'closed'].includes(t.status)) return false
    const remaining = new Date(t.sla_deadline).getTime() - Date.now()
    return remaining >= 0 && remaining <= 2 * 60 * 60 * 1000
  }).length
  const roleTitle = user.role === 'employee' ? 'Your support desk.' : user.role === 'engineer' ? 'Your assigned queue.' : 'Operations overview.'

  async function markRead(notificationId) {
    await api.readNotification(notificationId)
    reload()
  }

  async function changeRole(userId, role) {
    const updated = await api.updateUserRole(userId, role)
    setAdminUsers((current) => current.map((item) => item.id === updated.id ? updated : item))
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">HelpDesk<span>Pro</span></div>
        <div className="nav-label">Workspace</div>
        <button className="nav-item active">Overview</button>
        <button
          className="nav-item"
          onClick={() => document.querySelector('.tickets-panel')?.scrollIntoView({ behavior: 'smooth' })}
        >
          Tickets
        </button>
        <button
          className="nav-item"
          onClick={() => document.querySelector('.alerts-panel')?.scrollIntoView({ behavior: 'smooth' })}
        >
          Notifications {unreadCount > 0 ? `(${unreadCount})` : ''}
        </button>
        <div className="side-foot">
          Signed in as
          <br />
          <strong>{user.role}</strong>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <span className="eyebrow">HelpDeskPro / {user.role}</span>
          <div className="user-chip">
            <span>{user.name}</span>
            <span className="avatar">{user.name[0].toUpperCase()}</span>
            <button className="btn secondary small" onClick={onLogout}>Log out</button>
          </div>
        </header>

        <div className="content">
          <div className="intro">
            <div>
              <h1>{roleTitle}</h1>
              <p>Keep every request moving with clarity.</p>
            </div>
            {user.role === 'employee' && (
              <button className="btn" onClick={() => setShowCreate(true)}>+ New ticket</button>
            )}
          </div>

          {error && <div className="notice">{error}. Check that the FastAPI server is running.</div>}

          <div className="grid stats">
            <div className="stat">
              <span>Active tickets</span>
              <strong>{open}</strong>
            </div>
            <div className="stat">
              <span>Resolved</span>
              <strong>{resolved}</strong>
            </div>
            <div className="stat">
              <span>High priority</span>
              <strong>{urgent}</strong>
            </div>
            <div className="stat">
              <span>Unread alerts</span>
              <strong>{unreadCount}</strong>
            </div>
            {(user.role === 'manager' || user.role === 'admin') && (
              <div className="stat">
                <span>SLA risk / overdue</span>
                <strong>{atRisk} / {overdue}</strong>
              </div>
            )}
          </div>

          {analytics && (
            <section className="panel" style={{ marginBottom: 24 }}>
              <div className="panel-head"><h2>Operations analytics</h2><span className="muted">Average resolution: {analytics.average_resolution_hours}h</span></div>
              <div className="ticket-meta">
                <span className="badge open">{analytics.total} total</span>
                <span className="badge critical">{analytics.sla_breached} SLA breached</span>
                {Object.entries(analytics.by_category).map(([category, count]) => <span className="muted" key={category}>{category}: {count}</span>)}
              </div>
            </section>
          )}

          {user.role === 'admin' && (
            <section className="panel" style={{ marginBottom: 24 }}>
              <div className="panel-head"><h2>User administration</h2><span className="muted">Manage access levels</span></div>
              {adminUsers.map((managedUser) => (
                <div className="ticket" key={managedUser.id}>
                  <div><strong>{managedUser.name}</strong><div className="muted">{managedUser.email}</div></div>
                  <select value={managedUser.role} onChange={(event) => changeRole(managedUser.id, event.target.value)}>
                    <option value="employee">Employee</option>
                    <option value="engineer">Engineer</option>
                    <option value="manager">Manager</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              ))}
            </section>
          )}

          <div className="grid layout">
            <section className="panel tickets-panel">
              <div className="panel-head">
                <h2>{user.role === 'employee' ? 'Your tickets' : 'Assigned tickets'}</h2>
                <select style={{ width: 145 }} value={status} onChange={(e) => setStatus(e.target.value)}>
                  <option value="">All status</option>
                  <option value="open">Open</option>
                  <option value="in_progress">In progress</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
              </div>

              {tickets.length ? (
                tickets.map((ticket) => (
                  <div className="ticket" key={ticket.id} style={{ cursor: 'pointer' }} onClick={() => setSelected(ticket)}>
                    <div>
                      <h3>{ticket.title}</h3>
                      <p>{ticket.description}</p>
                      <div className="ticket-meta">
                        <span className={`badge ${ticket.priority}`}>{ticket.priority}</span>
                        <span className={`badge ${ticket.status}`}>{ticket.status.replace('_', ' ')}</span>
                        {ticket.sla_deadline && (
                          <span className={`badge ${new Date(ticket.sla_deadline) < new Date() && !['resolved', 'closed'].includes(ticket.status) ? 'critical' : 'open'}`}>
                            {new Date(ticket.sla_deadline) < new Date() && !['resolved', 'closed'].includes(ticket.status) ? 'SLA overdue' : `SLA ${new Date(ticket.sla_deadline).toLocaleDateString()}`}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="muted">#{ticket.id}</div>
                  </div>
                ))
              ) : (
                <div className="empty">No tickets found.</div>
              )}
            </section>

            <aside className="panel alerts-panel">
              <div className="panel-head">
                <h2>Alerts</h2>
              </div>

              {notifications.length ? (
                notifications.map((notification) => (
                  <div
                    key={notification.id}
                    style={{
                      padding: '12px 0',
                      borderTop: '1px solid #ecebe5',
                      display: 'grid',
                      gap: 8
                    }}
                  >
                    <div>
                      <strong>{notification.title || 'Update'}</strong>
                    </div>
                    <div className="muted" style={{ fontSize: 13 }}>{notification.message}</div>
                    {!notification.is_read && (
                      <button className="btn secondary small" onClick={() => markRead(notification.id)}>
                        Mark read
                      </button>
                    )}
                  </div>
                ))
              ) : (
                <div className="empty">No notifications yet.</div>
              )}
            </aside>
          </div>
        </div>
      </main>

      {showCreate && (
        <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && setShowCreate(false)}>
          <section className="modal">
            <div className="panel-head">
              <h2>New ticket</h2>
              <button className="btn secondary small" onClick={() => setShowCreate(false)}>Close</button>
            </div>
            <TicketForm onCreated={async () => { setShowCreate(false); await reload() }} />
          </section>
        </div>
      )}

      {selected && (
        <TicketDetail
          ticket={selected}
          user={user}
          engineers={engineers}
          onClose={() => setSelected(null)}
          onRefresh={reload}
        />
      )}
    </div>
  )
}
