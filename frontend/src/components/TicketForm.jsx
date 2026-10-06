import { useState } from 'react'
import { api } from '../services/api'

const emptyForm = { title: '', description: '', category: '', priority: 'medium' }

export default function TicketForm({ onCreated }) {
  const [form, setForm] = useState(emptyForm)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [suggestion, setSuggestion] = useState(null)
  const [suggesting, setSuggesting] = useState(false)

  async function suggest() {
    if (form.title.length < 3 || form.description.length < 10) {
      setError('Add a subject and description first.')
      return
    }
    setSuggesting(true)
    setError('')
    try {
      const result = await api.suggestTicket(form)
      setSuggestion(result)
      setForm((current) => ({ ...current, category: result.category, priority: result.priority }))
    } catch (err) {
      setError(err.message)
    } finally {
      setSuggesting(false)
    }
  }

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')

    try {
      await api.createTicket(form)
      setForm(emptyForm)
      onCreated()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit}>
      <div className="field">
        <label>SUBJECT</label>
        <input
          required
          minLength="5"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          placeholder="What do you need help with?"
        />
      </div>

      <div className="field">
        <label>DESCRIPTION</label>
        <textarea
          required
          minLength="10"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          placeholder="Add useful context for the support team"
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <div className="field">
          <label>CATEGORY</label>
          <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            <option value="">Auto-detect with AI</option>
            <option>Hardware</option>
            <option>Software</option>
            <option>Access</option>
            <option>Network</option>
            <option>Other</option>
          </select>
        </div>

        <div className="field">
          <label>PRIORITY</label>
          <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      <button type="button" className="btn secondary" onClick={suggest} disabled={suggesting}>
        {suggesting ? 'Analyzing...' : 'Suggest category & priority'}
      </button>
      {suggestion && (
        <div className="notice" style={{ marginTop: 12 }}>
          <strong>{suggestion.category} / {suggestion.priority}</strong> ({Math.round(suggestion.confidence * 100)}% confidence)
          <div>{suggestion.troubleshooting.join(' • ')}</div>
          <small>{suggestion.disclaimer}</small>
        </div>
      )}

      {error && <p className="error">{error}</p>}
      <button className="btn" disabled={busy}>
        {busy ? 'Creating...' : 'Create ticket'}
      </button>
    </form>
  )
}
