import React, { useEffect, useState, useCallback } from 'react'
import { ChatIcon, SearchIcon, MicIcon, ImageIcon, CloseIcon } from './icons'

export default function IntelligenceDashboard({ baseUrl = 'http://127.0.0.1:6060', onNavigate }) {
  const [health, setHealth] = useState('unknown')
  const [voice, setVoice] = useState(null)
  const [autoUpdate, setAutoUpdate] = useState(false)
  const [voiceEvents, setVoiceEvents] = useState(true)
  const [notifications, setNotifications] = useState(true)
  const [imagesOpen, setImagesOpen] = useState(false)

  useEffect(() => {
    (async () => {
      try {
        await fetch(`${baseUrl}/health`).then(r => r.json())
        setHealth('ok')
      } catch {
        setHealth('error')
      }
      try {
        const vs = await fetch(`${baseUrl}/voice/status`).then(r => r.json())
        setVoice(vs)
        setVoiceEvents(Boolean(vs?.voice_feedback_enabled !== false))
      } catch {
        setVoice(null)
      }
      try {
        const cfg = await fetch(`${baseUrl}/config`).then(r => r.json())
        setAutoUpdate(Boolean(cfg?.auto_update))
      } catch (err) { console.debug('Config fetch failed', err) }
    })()
  }, [baseUrl])

  const goChat = useCallback(() => onNavigate ? onNavigate('Chat') : console.debug('Navigate Chat'), [onNavigate])
  const goSearch = useCallback(() => onNavigate ? onNavigate('Browser') : console.debug('Navigate Search'), [onNavigate])
  const toggleMic = useCallback(async () => {
    try {
      const res = await fetch(`${baseUrl}/config`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enable_voice_mode: !(voice?.enable_voice_mode) }) })
      const data = await res.json()
      setVoice((v) => ({ ...(v || {}), enable_voice_mode: Boolean(data.enable_voice_mode) }))
    } catch (err) {
      console.warn('Failed to toggle voice mode', err)
    }
  }, [baseUrl, voice])

  const toggleAutoUpdate = useCallback(async () => {
    try {
      const res = await fetch(`${baseUrl}/config`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ auto_update: !autoUpdate }) })
      const data = await res.json()
      setAutoUpdate(Boolean(data.auto_update))
    } catch (err) { console.warn('Failed to toggle auto update', err) }
  }, [baseUrl, autoUpdate])

  const toggleVoiceEvents = useCallback(async () => {
    try {
      const res = await fetch(`http://127.0.0.1:5050/voice/config`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ voice_feedback_enabled: !voiceEvents }) })
      const data = await res.json()
      setVoiceEvents(Boolean(data.voice_feedback_enabled !== false))
    } catch (err) { console.warn('Failed to toggle voice events', err) }
  }, [voiceEvents])

  const NeonCard = ({ title, children }) => (
    <div className="neon-card">
      <div className="neon-card__title">{title}</div>
      {children}
    </div>
  )

  const BigButton = ({ label, onClick, icon }) => (
    <button className="big-button" onClick={onClick}>
      {icon} <span>{label}</span>
    </button>
  )

  return (
    <div style={{ padding: 18, background: 'var(--bg)', color: 'var(--text)' }}>
      <div className="grid-2">
        <div>
          <NeonCard title="CHAT">
            <div className="chat-header">
              <div className="avatar pulse-glow" />
              <div style={{ flex: 1 }}>
                <div style={{ opacity: 0.8, fontSize: 12 }}>Assistant</div>
                <div style={{ fontSize: 14 }}>How can I help you?</div>
              </div>
            </div>
            <div className="btn-row">
              <BigButton label="CHAT" icon={<ChatIcon />} onClick={goChat} />
              <BigButton label="SEARCH" icon={<SearchIcon />} onClick={goSearch} />
            </div>
          </NeonCard>

          <div style={{ marginTop: 16 }}>
            <NeonCard title="SETTINGS">
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <input type="checkbox" checked={autoUpdate} onChange={toggleAutoUpdate} /> Auto Update
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <input type="checkbox" checked={voiceEvents} onChange={toggleVoiceEvents} /> Voice Events
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <input type="checkbox" checked={notifications} onChange={() => setNotifications(v => !v)} /> Notifications
                </label>
                <button onClick={toggleMic} title="Toggle Voice Mode" className="neon-button icon-only" aria-label="Toggle voice mode">
                  <MicIcon />
                </button>
              </div>
            </NeonCard>
          </div>
        </div>

        <div>
          <NeonCard title="IMAGES">
            <div className="images-header">
              <div className="image-thumb" />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, opacity: 0.8 }}>Recent activity</div>
                <div style={{ display: 'flex', gap: 10, marginTop: 6 }}>
                  <div>Items: <strong>{String(voice?.vector_count ?? '—')}</strong></div>
                  <div>Health: <strong>{health}</strong></div>
                </div>
              </div>
              <button className="neon-button" onClick={() => setImagesOpen(true)}>
                <ImageIcon style={{ marginRight: 6 }} /> Open
              </button>
            </div>
          </NeonCard>

          {imagesOpen && (
            <div className="drawer">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong>Images</strong>
                <button className="neon-button" onClick={() => setImagesOpen(false)} aria-label="Close images">
                  <CloseIcon style={{ marginRight: 6 }} /> Close
                </button>
              </div>
              <div style={{ opacity: 0.8, marginTop: 8 }}>Gallery coming soon.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}