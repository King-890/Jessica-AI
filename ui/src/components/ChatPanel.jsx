import { useEffect, useState } from 'react'
import { api } from '../utils/apiClient'

export default function ChatPanel({ baseUrl = 'http://127.0.0.1:6060' }) {
  const [token, setToken] = useState('')
  const [message, setMessage] = useState('Hello Jessica')
  const [response, setResponse] = useState('')
  const [err, setErr] = useState('')
  const [recall, setRecall] = useState([])
  const [loadingRecall, setLoadingRecall] = useState(false)

  async function send() {
    setErr('')
    setResponse('')
    try {
      if (token) api.setToken(token)
      const r = await api.voiceCommand(message, baseUrl)
      if (!r.ok) throw new Error(r.json?.detail || 'HTTP error')
      setResponse(String((r.json?.response) || ''))
    } catch (e) {
      setErr(String(e))
    }
  }

  useEffect(() => {
    const q = message.trim()
    if (!q) { setRecall([]); return }
    setLoadingRecall(true)
    const t = setTimeout(async () => {
      try {
        const r = await api.memoryQuery(q, 5, baseUrl)
        setRecall(Array.isArray(r.json?.items) ? r.json.items : [])
      } catch {
        setRecall([])
      } finally {
        setLoadingRecall(false)
      }
    }, 250)
    return () => clearTimeout(t)
  }, [message, baseUrl])

  return (
    <div>
      <h4>Chat (Voice Command via Backend)</h4>
      <div className="input">
        <input value={token} onChange={(e) => setToken(e.target.value)} placeholder="Token" />
        <input value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Message" />
        <button onClick={send}>Send</button>
      </div>
      <div className="messages" style={{ marginTop: 8 }}>
        <div className="msg">
          <span className="label">context recall {loadingRecall ? '(loading...)' : ''}</span>
          <div>
            {recall.map((r) => (
              <div key={r.id} style={{ marginBottom: 6 }}>
                <small>{typeof r.score === 'number' ? r.score.toFixed(4) : r.score}</small>
                <div>{r.content}</div>
              </div>
            ))}
            {recall.length === 0 && !loadingRecall && <em>No similar memories found.</em>}
          </div>
        </div>
      </div>
      <small className="status">Hint: run scripts/make_token.ps1 to create a dev token. Token is stored locally.</small>
      {err && <p className="status err">{err}</p>}
      <div className="messages">
        <div className="msg">
          <span className="label">response</span>
          <span>{response}</span>
        </div>
      </div>
    </div>
  )
}