import { useEffect, useState } from 'react'
import { getLogs } from '@/api/apiClient'

type LogEntry = string

export default function LogsPanel() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [error, setError] = useState<string>('')

  useEffect(() => {
    let mounted = true
    let timer: any
    async function refresh() {
      try {
        const data = await getLogs()
        if (!mounted) return
        setLogs(Array.isArray(data) ? data : [])
        setError('')
      } catch (e: any) {
        setError(e?.message || 'Failed to fetch logs')
      }
    }
    refresh()
    timer = setInterval(refresh, 3000)
    return () => { mounted = false; if (timer) clearInterval(timer) }
  }, [])

  return (
    <div
      className="box"
      style={{ background: 'linear-gradient(180deg, #0b1d2a 0%, #0b1220 100%)', animation: 'drawerIn .2s ease-out' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0 }}>Recent Logs</h4>
        {error && <span className="status err">{error}</span>}
      </div>
      <div style={{ marginTop: 8, fontSize: 12, color: '#9ca3af' }}>Last ~50 entries, auto-refreshing</div>
      <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
        {logs.length === 0 && <div className="status">No logs available</div>}
        {logs.map((line, i) => {
          let parsed: any = null
          try { parsed = JSON.parse(line) } catch { /* ignore */ }
          return (
            <div key={i} className="neon-card" style={{ padding: 10, animation: 'drawerIn .18s ease-out' }}>
              <code style={{ fontFamily: 'monospace', fontSize: 12 }}>
                {parsed ? JSON.stringify(parsed) : line}
              </code>
            </div>
          )
        })}
      </div>
    </div>
  )
}