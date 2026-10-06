import { AuthProvider, useAuth } from './context/AuthContext'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'

function AppShell() {
  const { user, loading, login, logout } = useAuth()

  if (loading) {
    return (
      <main className="login-wrap">
        <section className="login-card">
          <div className="brand">HelpDesk<span>Pro</span></div>
          <p className="muted">Loading your workspace...</p>
        </section>
      </main>
    )
  }

  if (!user) return <LoginPage onLogin={login} />
  return <DashboardPage user={user} onLogout={logout} />
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  )
}
