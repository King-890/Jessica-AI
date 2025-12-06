import { useEffect, useState } from "react"
import { api } from "../utils/apiClient"
import { notifyConfigSaved, notifyError } from "../utils/trayNotifications"

export default function CombinedSettings({ backendUrl = "http://127.0.0.1:6060", internalUrl = "http://127.0.0.1:5050" }) {
  const [autoUpdate, setAutoUpdate] = useState(false)
  const [saveStatus, setSaveStatus] = useState("")
  const [token, setToken] = useState("")

  const [voiceStatus, setVoiceStatus] = useState(null)
  const [adapter, setAdapter] = useState('vosk')
  const [whisperModel, setWhisperModel] = useState('base')
  const [voskPath, setVoskPath] = useState('')
  const [voiceEvents, setVoiceEvents] = useState(true)
  const [moodProfile, setMoodProfile] = useState('neutral')
  const [err, setErr] = useState('')

  useEffect(() => {
    (async () => {
      try {
        const headers = {}
        const t = (typeof localStorage !== 'undefined' && localStorage.getItem('apiToken')) || ''
        if (t) headers['Authorization'] = 'Bearer ' + t
        const res = await fetch(backendUrl + "/config/", { headers })
        const data = await res.json()
        setAutoUpdate(Boolean(data.auto_update))
      } catch (err) {
        console.warn("Failed to fetch backend config", err)
      }
      try {
        const res = await fetch(internalUrl + "/voice/status")
        const data = await res.json()
        setVoiceStatus(data)
        setAdapter(String(data.stt_adapter || 'vosk'))
        setWhisperModel(String(data.whisper_model_name || 'base'))
        setVoskPath(String(data.vosk_model_path || ''))
        setVoiceEvents(Boolean(data.voice_feedback_enabled !== false))
        setMoodProfile(String(data.mood_profile || 'neutral'))
      } catch (e) {
        setErr(String(e))
      }
    })()
  }, [backendUrl, internalUrl])

  async function toggleUpdate() {
    try {
      const headers = { "Content-Type": "application/json" }
      const t = (typeof localStorage !== 'undefined' && localStorage.getItem('apiToken')) || ''
      if (t) headers['Authorization'] = 'Bearer ' + t
      const res = await fetch(backendUrl + "/config", {
        method: "POST",
        headers,
        body: JSON.stringify({ auto_update: !autoUpdate })
      })
      const data = await res.json()
      setAutoUpdate(Boolean(data.auto_update))
      setSaveStatus("Saved")
      notifyConfigSaved()
      setTimeout(() => setSaveStatus(""), 1500)
    } catch (e) {
      setSaveStatus("Failed to save")
      console.error(e)
      notifyError("Failed to save configuration")
    }
  }

  async function loadConfig() {
    try {
      if (token) api.setToken(token)
      const r = await api.getConfig(backendUrl)
      if (!r.ok) throw new Error(r.json?.detail || 'HTTP error')
      setAutoUpdate(Boolean(r.json?.auto_update))
      setSaveStatus("Loaded")
      setTimeout(() => setSaveStatus(""), 1500)
    } catch (e) {
      notifyError("Failed to load configuration")
    }
  }

  async function reloadBackendConfig() {
    try {
      if (token) api.setToken(token)
      const r = await api.reloadConfig(backendUrl)
      if (!r.ok) throw new Error(r.json?.detail || 'HTTP error')
      setSaveStatus("Reloaded")
      notifyConfigSaved()
      setTimeout(() => setSaveStatus(""), 1500)
    } catch (e) {
      notifyError("Failed to reload configuration")
    }
  }

  async function applyVoice() {
    setErr('')
    try {
      const res = await fetch(internalUrl + "/voice/config", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stt_adapter: adapter, whisper_model_name: whisperModel, vosk_model_path: voskPath, voice_feedback_enabled: voiceEvents, mood_profile: moodProfile })
      })
      const data = await res.json()
      setVoiceStatus(data)
      notifyConfigSaved()
    } catch (e) {
      setErr(String(e))
      notifyError("Failed to save voice settings")
    }
  }

  const whisperModels = (voiceStatus?.available_models?.whisper || ['tiny','base','small','medium','large'])
  const profiles = (voiceStatus?.available_profiles || ['neutral','confident','empathetic','assistive'])

  return (
    <div>
      <h3>Jessica Settings</h3>
      <div className="box" style={{ marginBottom: 10 }}>
        <h4>Auth</h4>
        <div className="input" style={{ alignItems: 'center' }}>
          <input value={token} onChange={(e) => setToken(e.target.value)} placeholder="Token" />
          <button onClick={() => { try { localStorage.setItem('apiToken', token || '') } catch {} }}>Use Token</button>
          <button style={{ marginLeft: 8 }} onClick={() => { try { localStorage.removeItem('apiToken'); setToken('') } catch {} }}>Clear</button>
        </div>
      </div>
      <div className="box">
        <h4>Updates</h4>
        <label>
          <input type="checkbox" checked={autoUpdate} onChange={toggleUpdate} /> Enable Auto Update
        </label>
        <div className="input" style={{ marginTop: 8 }}>
          <button onClick={loadConfig}>Load Config</button>
          <button style={{ marginLeft: 8 }} onClick={reloadBackendConfig}>Reload (admin)</button>
        </div>
        {saveStatus && <p className="status">{saveStatus}</p>}
      </div>
      <div className="box" style={{ marginTop: 10 }}>
        <h4>Voice</h4>
        <div className="input" style={{ alignItems: 'center' }}>
          <label>STT Adapter:&nbsp;
            <select value={adapter} onChange={(e) => setAdapter(e.target.value)}>
              <option value="vosk">Vosk</option>
              <option value="whisper">Whisper</option>
            </select>
          </label>
          {adapter === 'whisper' && (
            <label style={{ marginLeft: 8 }}>Model:&nbsp;
              <select value={whisperModel} onChange={(e) => setWhisperModel(e.target.value)}>
                {whisperModels.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            </label>
          )}
          {adapter === 'vosk' && (
            <input style={{ marginLeft: 8 }} value={voskPath} onChange={(e) => setVoskPath(e.target.value)} placeholder="VOSK_MODEL_PATH" />
          )}
          <label style={{ marginLeft: 8 }}>
            <input type="checkbox" checked={voiceEvents} onChange={(e) => setVoiceEvents(e.target.checked)} />
            Voice feedback for events
          </label>
          <label style={{ marginLeft: 8 }}>Mood profile:&nbsp;
            <select value={moodProfile} onChange={(e) => setMoodProfile(e.target.value)}>
              {profiles.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </label>
          <button style={{ marginLeft: 8 }} onClick={applyVoice}>Apply</button>
        </div>
        {err && <p className="status err">{err}</p>}
      </div>
    </div>
  )
}