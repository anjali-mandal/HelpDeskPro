import { useState } from 'react'
import { api } from '../services/api'

const demoAccounts = {
  employee: { email: 'employee@helpdeskpro.com', password: 'employee123' },
  engineer: { email: 'engineer@helpdeskpro.com', password: 'engineer123' },
  manager: { email: 'manager@helpdeskpro.com', password: 'manager123' }
}

export default function LoginForm({ onLogin }) {
  const [mode, setMode] = useState('login')
  const [selectedRole, setSelectedRole] = useState('employee')
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setError('')
    setBusy(true)

    try {
      if (mode === 'register') {
        await api.register(form)
      }

      await onLogin({
        email: form.email,
        password: form.password
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-wrap">
      <section className="login-card">
        <div className="brand">HelpDesk<span>Pro</span></div>
        <h1>{mode === 'login' ? 'Welcome back.' : 'Create your account.'}</h1>
        <p className="muted">
          {mode === 'login'
            ? 'Sign in to manage your support desk.'
            : 'Employee accounts are ready in under a minute.'}
        </p>

        <form onSubmit={submit}>
          {mode === 'login' && (
            <div className="field">
              <label>LOGIN AS</label>
              <select
                value={selectedRole}
                onChange={(e) => {
                  const role = e.target.value
                  setSelectedRole(role)
                  setForm({ ...form, ...demoAccounts[role] })
                }}
              >
                <option value="employee">Employee</option>
                <option value="engineer">IT Engineer</option>
                <option value="manager">Manager</option>
              </select>
            </div>
          )}
          {mode === 'register' && (
            <div className="field">
              <label>FULL NAME</label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
          )}

          <div className="field">
            <label>WORK EMAIL</label>
            <input
              required
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </div>

          <div className="field">
            <label>PASSWORD</label>
            <input
              required
              minLength="6"
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </div>

          {error && <p className="error">{error}</p>}

          <button className="btn" disabled={busy} style={{ width: '100%' }}>
            {busy ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <button
          className="btn secondary"
          style={{ width: '100%', marginTop: 12 }}
          onClick={() => {
            setMode(mode === 'login' ? 'register' : 'login')
            setError('')
          }}
        >
          {mode === 'login' ? 'New here? Register' : 'Already have an account? Sign in'}
        </button>

        {mode === 'login' && (
          <div style={{ marginTop: 20, padding: 14, borderRadius: 12, background: '#eef5f1', border: '1px solid #dfeae4' }}>
            <strong style={{ display: 'block', marginBottom: 8 }}>Demo users</strong>
            <div style={{ fontSize: 12, lineHeight: 1.7 }}>
              <div><strong>Employee:</strong> employee@helpdeskpro.com / employee123</div>
              <div><strong>Engineer:</strong> engineer@helpdeskpro.com / engineer123</div>
              <div><strong>Manager:</strong> manager@helpdeskpro.com / manager123</div>
            </div>
          </div>
        )}
      </section>
    </main>
  )
}
