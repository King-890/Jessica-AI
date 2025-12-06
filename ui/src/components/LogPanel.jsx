import React, { useEffect, useState, useCallback } from 'react'

export default function LogPanel({ systemUrl = 'http://127.0.0.1:6060' }) {
  const [system, setSystem] = useState(null)
  const [err, setErr] = useState('')

  const refreshSystem = useCallback(async () => {
    try {
      const res = await fetch(`${systemUrl}/system/status`)
      const data = await res.json()
      setSystem(data)
    } catch (e) {
      setErr(String(e))
    }
  }, [systemUrl])

  useEffect(() => { refreshSystem() }, [refreshSystem])

  return (
    <div>
      <h4>System Status</h4>
      {err && <p className="status err">{err}</p>}
      {system && (
        <div>
          <p className="status">CPU: {system.cpu_percent}% — Memory: {system.memory_percent}%</p>
          <div className="messages">
            {(system.processes || []).map((p) => (
              <div key={p.pid} className="msg">
                <span className="label">PID {p.pid}</span>
                <p>{p.name} — CPU {p.cpu}% — MEM {p.mem}%</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}