import React, { useEffect, useState, useCallback } from 'react'
import { notify } from '../utils/trayNotifications'
import { getConfig, setConfig } from '@/api/apiClient'

export default function VoiceControlPanel({ backendUrl = 'http://127.0.0.1:6060' }) {
  const [voiceEnabled, setVoiceEnabled] = useState(false)
  const [loading, setLoading] = useState(false)
  const [conn, setConn] = useState('disconnected')

  const refresh = useCallback(async () => {
    try {
      const cfg = await getConfig()
      setVoiceEnabled(Boolean(cfg.enable_voice_mode))
      setConn('connected')
    } catch (e) {
      // Axios errors include status. Treat 401 distinctly.
      const status = e?.response?.status
      setConn(status === 401 ? 'unauthorized' : 'disconnected')
    }
  }, [])

  async function toggle() {
    setLoading(true)
    try {
      const json = await setConfig({ enable_voice_mode: !voiceEnabled })
      const enabled = Boolean(json.enable_voice_mode)
      setVoiceEnabled(enabled)
      notify('Voice Mode', enabled ? 'Voice mode enabled' : 'Voice mode disabled')
      setConn('connected')
    } catch (e) {
      const status = e?.response?.status
      setConn(status === 401 ? 'unauthorized' : 'disconnected')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [refresh])

  return (
    <div>
      <h4>Voice Control</h4>
      <div className="input" style={{ alignItems: 'center' }}>
        <button className="btn" onClick={toggle} disabled={loading}>
          {voiceEnabled ? '🎙️ Voice Mode: On' : '🎙️ Voice Mode: Off'}
        </button>
        <span className={`status ${conn === 'unauthorized' ? 'err' : ''}`} style={{ marginLeft: 8 }}>
          {conn === 'connected' ? '🔗 Connected (200 OK)' : conn === 'unauthorized' ? '⚠️ Unauthorized (401)' : '💤 Disconnected'}
        </span>
      </div>
      <small className="status">Wake Phrase: "Hey Jessica" (configurable in configs/voice_settings.yaml)</small>
    </div>
  )
}