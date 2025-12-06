import { useEffect, useState, useCallback } from 'react'

export default function KnowledgePanel({ baseUrl = 'http://127.0.0.1:6060' }) {
  const [q, setQ] = useState('')
  const [results, setResults] = useState([])
  const [err, setErr] = useState('')

  const search = useCallback(async () => {
    setErr('')
    try {
      const res = await fetch(baseUrl + '/memory/search?q=' + encodeURIComponent(q) + '&k=8')
      const data = await res.json()
      setResults(Array.isArray(data.items) ? data.items : [])
    } catch (e) {
      setErr(String(e))
    }
  }, [q, baseUrl])

  useEffect(() => { if (q.length >= 2) { const t = setTimeout(search, 300); return () => clearTimeout(t) } }, [q, search])

  return (
    <div>
      <h4>Knowledge & Semantic Memory</h4>
      <div className="input">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search memories or knowledge" />
        <button onClick={search}>Search</button>
      </div>
      {err && <p className="status err">{err}</p>}
      <div className="messages">
        {results.map((r) => (
          <div key={r.id} className="msg">
            <span className="label">score {typeof r.score === 'number' ? r.score.toFixed(4) : r.score}</span>
            <div>{r.content}</div>
          </div>
        ))}
        {results.length === 0 && !err && (
          <div className="msg"><em>No results yet. Try searching for a recent chat phrase.</em></div>
        )}
      </div>
    </div>
  )
}