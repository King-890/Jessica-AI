import React, { useEffect, useRef, useState } from 'react'
import Button from '@/components/Button'

type Props = {
  backendBase?: string
  room?: string
  user?: string
}

export default function CodeEditor({ backendBase = 'http://127.0.0.1:6060', room = 'default', user = 'user' }: Props) {
  const [text, setText] = useState('')
  const [conn, setConn] = useState<'disconnected'|'connected'|'error'>('disconnected')
  const [suggestion, setSuggestion] = useState('')
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    try {
      const wsUrl = backendBase.replace('http', 'ws') + `/ide/ws?room=${encodeURIComponent(room)}`
      const ws = new WebSocket(wsUrl)
      ws.onopen = () => setConn('connected')
      ws.onerror = () => setConn('error')
      ws.onclose = () => setConn('disconnected')
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data)
          if (msg.type === 'sync' || msg.type === 'change') {
            setText(String(msg.buffer || ''))
          }
        } catch {}
      }
      wsRef.current = ws
      return () => { try { ws.close() } catch {} }
    } catch { setConn('error') }
  }, [backendBase, room])

  function broadcast(newText: string) {
    try { wsRef.current?.send(JSON.stringify({ type: 'change', buffer: newText })) } catch {}
  }

  async function askAI() {
    try {
      const res = await fetch(backendBase + '/ide/assist', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'Improve or complete code', language: 'javascript', context: text })
      })
      const data = await res.json().catch(() => ({}))
      setSuggestion(String(data?.suggestion || ''))
    } catch (e) {
      setSuggestion('Assistant request failed')
    }
  }

  return (
    <div className="box" style={{ background: '#0b1d2a', borderColor: 'var(--neon-border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0 }}>Collaborative Editor</h4>
        <span className={`status ${conn === 'connected' ? 'ok' : conn === 'error' ? 'err' : ''}`}>WS: {conn}</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 12, marginTop: 12 }}>
        <textarea
          value={text}
          onChange={(e) => { const v = e.target.value; setText(v); broadcast(v) }}
          placeholder="Type code here and share in real-time..."
          style={{ minHeight: 260, background: '#072032', color: '#aef', border: '1px solid var(--neon-border)', borderRadius: 8, padding: 10, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace' }}
        />
        <div className="neon-card" style={{ animation: 'none' }}>
          <div className="neon-card__title">AI Assistance</div>
          <div style={{ fontSize: 12, color: '#9ca3af' }}>Generates suggestions based on current buffer.</div>
          <div style={{ marginTop: 10 }}>
            <Button variant="neon" onClick={askAI}>Ask AI</Button>
          </div>
          <div style={{ marginTop: 10, maxHeight: 200, overflow: 'auto', whiteSpace: 'pre-wrap' }}>
            {suggestion ? suggestion : <span className="status">No suggestion yet</span>}
          </div>
        </div>
      </div>
    </div>
  )
}