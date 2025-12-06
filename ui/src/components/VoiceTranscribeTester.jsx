import { useEffect, useRef, useState } from 'react'

export default function VoiceTranscribeTester({ baseUrl = 'http://127.0.0.1:5050' }) {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)
  const [recording, setRecording] = useState(false)
  const recRef = useRef(null)
  const chunksRef = useRef([])
  const streamRef = useRef(null)

  async function upload() {
    if (!file) return
    setLoading(true)
    setErr('')
    setResult('')
    try {
      const fd = new FormData()
      fd.append('audio', file)
      const headers = {}
      const t = (typeof localStorage !== 'undefined' && localStorage.getItem('apiToken')) || ''
      if (t) headers['Authorization'] = 'Bearer ' + t
      const res = await fetch(baseUrl + '/voice/transcribe', { method: 'POST', body: fd, headers })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.error || data.detail || ('HTTP ' + res.status))
      setResult(String(data.text || ''))
    } catch (e) {
      setErr(String(e))
    } finally {
      setLoading(false)
    }
  }

  async function startRec() {
    setErr('')
    setResult('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      chunksRef.current = []
      mr.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunksRef.current.push(e.data) }
      mr.onstop = async () => {
        try {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
          const fileObj = new File([blob], 'recording.webm', { type: 'audio/webm' })
          setFile(fileObj)
        } catch (e) { setErr(String(e)) }
      }
      mr.start()
      recRef.current = mr
      streamRef.current = stream
      setRecording(true)
    } catch (e) { setErr(String(e)) }
  }

  async function stopRec() {
    try { recRef.current?.stop() } catch {}
    try { streamRef.current?.getTracks()?.forEach((t) => t.stop()) } catch {}
    setRecording(false)
  }

  return (
    <div>
      <h4>Voice Transcribe Tester</h4>
      <div className="input" style={{ alignItems: 'center' }}>
        <input type="file" accept="audio/*" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button onClick={upload} disabled={loading || !file}>{loading ? 'Transcribing…' : 'Transcribe'}</button>
        <button onClick={startRec} disabled={recording} style={{ marginLeft: 8 }}>Push-to-Talk</button>
        <button onClick={stopRec} disabled={!recording}>Stop</button>
      </div>
      {err && <p className="status err">{err}</p>}
      {result && (
        <div className="messages" style={{ marginTop: 8 }}>
          <div className="msg"><span className="label">text</span><span>{result}</span></div>
        </div>
      )}
    </div>
  )
}