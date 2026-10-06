import { useEffect, useState } from 'react'
import { api } from '../services/api'

export default function TicketDetail({ ticket, user, engineers = [], onClose, onRefresh }) {
  const [comments, setComments] = useState([])
  const [availableEngineers, setAvailableEngineers] = useState(engineers)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [engineerId, setEngineerId] = useState(ticket.assigned_to || '')
  const [attachments, setAttachments] = useState([])
  const [history, setHistory] = useState([])
  const [attachmentError, setAttachmentError] = useState('')

  useEffect(() => {
    api.comments(ticket.id).then(setComments).catch(() => {})
    api.attachments(ticket.id).then(setAttachments).catch(() => {})
    api.history(ticket.id).then(setHistory).catch(() => {})
    if (['manager', 'admin'].includes(user.role)) {
      api.engineers().then(setAvailableEngineers).catch(() => {})
    }
  }, [ticket.id, user.role])

  useEffect(() => {
    setEngineerId(ticket.assigned_to || '')
  }, [ticket.assigned_to])

  async function addComment(event) {
    event.preventDefault()
    if (!message.trim()) return

    setBusy(true)
    try {
      const result = await api.addComment(ticket.id, message)
      setComments((current) => [...current, result])
      setMessage('')
      onRefresh()
    } finally {
      setBusy(false)
    }
  }

  async function changeStatus(status) {
    await api.updateTicket(ticket.id, { status })
    onRefresh()
    onClose()
  }

  async function changePriority(priority) {
    await api.updateTicket(ticket.id, { priority })
    onRefresh()
    onClose()
  }

  async function assign() {
    if (!engineerId) return
    await api.assignTicket(ticket.id, Number(engineerId))
    onRefresh()
    onClose()
  }

  async function uploadAttachment(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setAttachmentError('')
    try {
      const attachment = await api.uploadAttachment(ticket.id, file)
      setAttachments((current) => [...current, attachment])
      setHistory(await api.history(ticket.id))
    } catch (error) {
      setAttachmentError(error.message)
    } finally {
      event.target.value = ''
    }
  }

  async function downloadAttachment(attachment) {
    try {
      const blob = await api.downloadAttachment(attachment.id)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = attachment.file_name
      link.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      setAttachmentError(error.message)
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <section className="modal">
        <div className="panel-head">
          <div>
            <span className={`badge ${ticket.status}`}>{ticket.status.replace('_', ' ')}</span>
            <h2 style={{ marginTop: 10 }}>{ticket.title}</h2>
          </div>
          <button className="btn secondary small" onClick={onClose}>Close</button>
        </div>

        <p className="muted">{ticket.description}</p>

        <div className="ticket-meta">
          <span className={`badge ${ticket.priority}`}>{ticket.priority} priority</span>
          <span className="muted">#{ticket.id} · {ticket.category}</span>
          {ticket.sla_deadline && (
            <span className="muted">SLA: {new Date(ticket.sla_deadline).toLocaleString()}</span>
          )}
        </div>

        <hr style={{ border: 0, borderTop: '1px solid #e5e7e1', margin: '22px 0' }} />

        <h3>Conversation</h3>
        {comments.length ? (
          comments.map((comment) => (
            <div className="comment" key={comment.id}>
              <strong>{comment.user_name || 'User'}</strong>
              {comment.message}
            </div>
          ))
        ) : (
          <div className="empty">No comments yet.</div>
        )}

        <form onSubmit={addComment} style={{ marginTop: 18 }}>
          <div className="field">
            <label>ADD COMMENT</label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Write an update..."
            />
          </div>
          <button className="btn small" disabled={busy}>Post comment</button>
        </form>

        <div style={{ marginTop: 24 }}>
          <h3>Attachments</h3>
          {attachments.map((attachment) => (
            <button
              className="btn secondary small"
              key={attachment.id}
              onClick={() => downloadAttachment(attachment)}
              style={{ margin: '8px 8px 0 0' }}
            >
              {attachment.file_name}
            </button>
          ))}
          <div className="field" style={{ marginTop: 12 }}>
            <label>ADD FILE</label>
            <input type="file" accept="image/jpeg,image/png,application/pdf,text/plain" onChange={uploadAttachment} />
          </div>
          {attachmentError && <p className="error">{attachmentError}</p>}
        </div>

        <div style={{ marginTop: 24 }}>
          <h3>Activity</h3>
          {history.length ? history.map((item) => (
            <div className="comment" key={item.id}>
              <strong>{item.action.replace('_', ' ')}</strong>
              <span className="muted">{item.description}</span>
            </div>
          )) : <div className="empty">No activity yet.</div>}
        </div>

        {user.role !== 'employee' && (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
            {['manager', 'admin'].includes(user.role) && (
              <>
                <select value={ticket.priority} onChange={(e) => changePriority(e.target.value)}>
                  <option value="low">Low priority</option>
                  <option value="medium">Medium priority</option>
                  <option value="high">High priority</option>
                  <option value="critical">Critical priority</option>
                </select>
                <select
                  value={engineerId}
                  onChange={(e) => setEngineerId(e.target.value)}
                  style={{ width: 190 }}
                >
                  <option value="">Assign engineer...</option>
                  {availableEngineers.map((engineer) => (
                    <option value={engineer.id} key={engineer.id}>{engineer.name}</option>
                  ))}
                </select>
                <button className="btn secondary" onClick={assign}>Assign</button>
              </>
            )}

            {user.role === 'engineer' && ['open', 'assigned'].includes(ticket.status) && ticket.assigned_to === user.id && (
              <button className="btn" onClick={() => changeStatus('in_progress')}>
                Accept ticket
              </button>
            )}

            {ticket.status !== 'resolved' && (
              <button className="btn secondary" onClick={() => changeStatus('resolved')}>
                Mark resolved
              </button>
            )}
          </div>
        )}
      </section>
    </div>
  )
}
