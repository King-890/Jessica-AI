import { useEffect, useState } from 'react'
import { notifyHighCpu, notifyHighRam } from '../utils/trayNotifications'

export default function LiveLogs({ baseUrl = 'http://127.0.0.1:6060' }) {
  const [status, setStatus] = useState({ cpu_percent: 0, memory_percent: 0, processes: [] })
  const [connected, setConnected] = useState(false)
  const [paused, setPaused] = useState(false)
  const [esRef, setEsRef] = useState(null)

  useEffect(() => {
    const url = baseUrl + '/logs/stream'
    if (paused) return
    const es = new EventSource(url)
    setEsRef(es)
    es.onopen = () => setConnected(true)
    es.onerror = () => setConnected(false)
    es.onmessage = (ev) => {
      try {
        const payload = JSON.parse(ev.data)
        if (payload?.type === 'system_status') {
          const data = payload.data || {}
          setStatus({
            cpu_percent: Number(data.cpu_percent || 0),
            memory_percent: Number(data.memory_percent || 0),
            processes: Array.isArray(data.processes) ? data.processes : [],
          })
          if (Number(data.cpu_percent || 0) >= 85) notifyHighCpu(Number(data.cpu_percent || 0))
          if (Number(data.memory_percent || 0) >= 90) notifyHighRam(Number(data.memory_percent || 0))
        }
      } catch (err) {
        console.warn('Failed to parse logs event', err)
      }
    }
    return () => {
      try { es.close() } catch (err) { console.debug('Failed to close EventSource', err) }
    }
  }, [baseUrl, paused])

  useEffect(() => {
    if (paused && esRef) {
      try { esRef.close() } catch (err) { console.debug('Failed to close EventSource on pause', err) }
      setConnected(false)
    }
  }, [paused, esRef])

  return (
    <div>
      <h4>Live System Metrics {connected ? '• Connected' : '• Reconnecting...'}
        <button style={{ marginLeft: 8 }} onClick={() => setPaused(p => !p)}>{paused ? 'Resume' : 'Pause'}</button>
      </h4>
      <div style={{ display: 'flex', gap: 20 }}>
        <div className="metric">
          <div className="label">CPU</div>
          <div className="value">{status.cpu_percent.toFixed(1)}%</div>
        </div>
        <div className="metric">
          <div className="label">Memory</div>
          <div className="value">{status.memory_percent.toFixed(1)}%</div>
        </div>
      </div>
      <div style={{ marginTop: 10 }}>
        <h5>Top Processes</h5>
        <div className="messages">
          {status.processes.map((p) => (
            <div key={p.pid} className="msg">
              <span className="label">PID {p.pid}</span>
              <strong>{p.name || 'unknown'}</strong>
              <span style={{ marginLeft: 8 }}>CPU: {Number(p.cpu || 0).toFixed(1)}%</span>
              <span style={{ marginLeft: 8 }}>MEM: {Number(p.mem || 0).toFixed(1)}%</span>
            </div>
          ))}
          {status.processes.length === 0 && (
            <div className="msg"><em>No process data yet.</em></div>
          )}
        </div>
      </div>
    </div>
  )
}