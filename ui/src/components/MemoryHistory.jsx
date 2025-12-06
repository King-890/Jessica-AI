import { useEffect, useState, useCallback } from 'react'
import { api } from '../utils/apiClient'
import { notifyError } from '../utils/trayNotifications'

export default function MemoryHistory({ baseUrl = 'http://127.0.0.1:6060', refreshMs = 10000 }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const r = await api.memoryQuery('', 100, baseUrl)
      if (!r.ok) throw new Error(r.json?.detail || 'HTTP error')
      setItems(Array.isArray(r.json?.items) ? r.json.items : [])
    } catch {
      notifyError('Failed to load memory history')
    } finally {
      setLoading(false)
    }
  }, [baseUrl])

  useEffect(() => {
    load()
    const t = setInterval(load, refreshMs)
    return () => clearInterval(t)
  }, [load, refreshMs])

  return (
    <div>
      <h4>Interaction Memory History</h4>
      {loading && <p>Loading…</p>}
      <div className="messages">
        {items.map((it) => (
          <div key={it.id} className="msg">
            <span className="label">{it.time}</span>
            <div>
              <strong>Prompt:</strong>
              <div>{it.prompt}</div>
            </div>
            <div style={{ marginTop: 6 }}>
              <strong>Response:</strong>
              <div>{it.response}</div>
            </div>
          </div>
        ))}
        {items.length === 0 && !loading && (
          <div className="msg"><em>No interactions stored yet.</em></div>
        )}
      </div>
    </div>
  )
}