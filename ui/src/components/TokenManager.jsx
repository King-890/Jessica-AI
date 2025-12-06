import { useEffect, useState } from 'react'
import { activeTokenSource } from '../utils/apiClient'

export default function TokenManager() {
  const [token, setToken] = useState('')
  const [status, setStatus] = useState('')
  const [source, setSource] = useState('none')

  useEffect(() => {
    try { setToken(localStorage.getItem('apiToken') || '') } catch {}
    setSource(activeTokenSource())
  }, [])

  function save() {
    try {
      localStorage.setItem('apiToken', token || '')
      setSource(activeTokenSource())
      setStatus('Saved')
      setTimeout(() => setStatus(''), 1200)
    } catch { setStatus('Failed') }
  }
  function clear() {
    try {
      // Clear both tokens simultaneously
      localStorage.removeItem('apiToken')
      localStorage.removeItem('supabase_token')
      setToken('')
      setSource(activeTokenSource())
      setStatus('Cleared')
      setTimeout(() => setStatus(''), 1200)
    } catch { setStatus('Failed') }
  }

  return (
    <div className="box" style={{ marginBottom: 10 }}>
      <h4>API Token</h4>
      <div className="status" style={{ marginBottom: 6 }}>
        {source === 'supabase' && '🟢 Supabase Authenticated'}
        {source === 'dev' && '🟡 Local Dev Token'}
        {source === 'none' && '🔴 Unauthenticated'}
      </div>
      <div className="input" style={{ alignItems: 'center' }}>
        <input value={token} onChange={(e) => setToken(e.target.value)} placeholder="Token" />
        <button onClick={save}>Save</button>
        <button style={{ marginLeft: 8 }} onClick={clear}>Clear</button>
        {status && <span className="status" style={{ marginLeft: 8 }}>{status}</span>}
      </div>
      <small className="status">Stored in localStorage as 'apiToken'.</small>
    </div>
  )
}