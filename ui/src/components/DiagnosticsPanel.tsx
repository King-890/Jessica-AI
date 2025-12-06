import React, { useEffect, useState } from 'react'

type DiagnosticItem = {
  name: string
  status: string
  detail?: string
}

export function DiagnosticsPanel({ baseUrl = 'http://127.0.0.1:5050' }: { baseUrl?: string }) {
  const [items, setItems] = useState<DiagnosticItem[]>([])
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  async function runDiagnostics() {
    setRunning(true)
    setError('')
    try {
      const res = await fetch(`${baseUrl}/diagnostics/run`)
      const data = await res.json()
      if (data.detail) {
        setError(String(data.detail))
        setItems([])
      } else {
        const list: DiagnosticItem[] = (data.items || []).map((d: any) => ({
          name: String(d.name || 'check'),
          status: String(d.status || 'unknown'),
          detail: d.detail ? String(d.detail) : undefined,
        }))
        setItems(list)
      }
    } catch (e) {
      setError(String(e))
      setItems([])
    } finally {
      setRunning(false)
    }
  }

  useEffect(() => {
    runDiagnostics()
    const id = setInterval(runDiagnostics, 15000)
    return () => clearInterval(id)
  }, [])

  const ok = items.filter(i => i.status.toLowerCase() === 'ok').length
  const fail = items.filter(i => i.status.toLowerCase() !== 'ok').length

  return (
    <div>
      <h4>Problems & Diagnostics</h4>
      <div className="input" style={{ marginBottom: 8 }}>
        <button onClick={runDiagnostics} disabled={running}>{running ? 'Running…' : 'Run Now'}</button>
        <span style={{ marginLeft: 12 }} className="status">
          total: {items.length} • ok: {ok} • issues: {fail}
        </span>
      </div>
      {error && <p className="status err">{error}</p>}
      <div className="messages">
        {items.map((it, idx) => (
          <div key={idx} className="msg">
            <strong>{it.name}</strong> — {it.status}
            {it.detail && <p style={{ marginTop: 4 }}>{it.detail}</p>}
          </div>
        ))}
      </div>
    </div>
  )
}

export default DiagnosticsPanel