import { useCallback, useEffect, useState } from 'react'
import { api } from '../services/api'

export function useTickets(status = '', userRole = null) {
  const [tickets, setTickets] = useState([])
  const [notifications, setNotifications] = useState([])
  const [engineers, setEngineers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      setLoading(true)
      const [items, alerts, staff] = await Promise.all([
        api.tickets(status),
        api.notifications(),
        userRole && ['manager', 'admin'].includes(userRole) ? api.engineers() : Promise.resolve([])
      ])

      setTickets(items)
      setNotifications(alerts)
      setEngineers(staff || [])
      setError('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [status, userRole])

  useEffect(() => {
    load()
  }, [load])

  return { tickets, notifications, engineers, loading, error, reload: load }
}
