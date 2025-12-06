import { useEffect, useMemo, useState } from 'react'
import StatusCard from '@/components/StatusCard'
import LogsPanel from '@/components/LogsPanel'
import DiagnosticsPanel from '@/components/DiagnosticsPanel'
import { getStatus, getConfig } from '@/api/apiClient'

type StatusResp = { api_online: boolean; db_connected: boolean; uptime: number | null }

function ServerIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="3" y="4" width="18" height="6" rx="2" stroke="#aef"/>
      <rect x="3" y="14" width="18" height="6" rx="2" stroke="#aef"/>
      <circle cx="7" cy="7" r="1" fill="#aef"/>
      <circle cx="7" cy="17" r="1" fill="#aef"/>
    </svg>
  )
}

function DatabaseIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <ellipse cx="12" cy="5" rx="8" ry="3" stroke="#aef"/>
      <path d="M4 5v9c0 1.7 3.6 3 8 3s8-1.3 8-3V5" stroke="#aef"/>
      <path d="M4 10c0 1.7 3.6 3 8 3s8-1.3 8-3" stroke="#aef"/>
    </svg>
  )
}

function TimerIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="13" r="8" stroke="#aef"/>
      <path d="M9 3h6" stroke="#aef"/>
      <path d="M12 13l4-2" stroke="#aef"/>
    </svg>
  )
}

export default function Dashboard() {
  const [status, setStatus] = useState<StatusResp>({ api_online: false, db_connected: false, uptime: null })
  const [config, setConfig] = useState<any>({})
  const [error, setError] = useState<string>('')

  useEffect(() => {
    let mounted = true
    let timer: any
    async function refresh() {
      try {
        const s = await getStatus()
        const c = await getConfig()
        if (!mounted) return
        setStatus(s)
        setConfig(c)
        setError('')
      } catch (e: any) {
        setError(e?.message || 'Failed to fetch dashboard data')
      }
    }
    refresh()
    timer = setInterval(refresh, 5000)
    return () => { mounted = false; if (timer) clearInterval(timer) }
  }, [])

  const uptimeStr = useMemo(() => {
    const u = status.uptime
    if (!u || u <= 0) return '—'
    const secs = Math.floor(u)
    const h = Math.floor(secs / 3600)
    const m = Math.floor((secs % 3600) / 60)
    const s = secs % 60
    return `${h}h ${m}m ${s}s`
  }, [status.uptime])

  return (
    <div style={{ display: 'grid', gap: 16, gridTemplateColumns: '1fr', padding: 4 }}>
      <div style={{ display: 'grid', gap: 16, gridTemplateColumns: '1fr', animation: 'drawerIn .2s ease-out' }}>
        {/* Responsive: stack on mobile, 2x2 on desktop */}
        <div className="grid-2" style={{ gridTemplateColumns: '1fr 1fr' }}>
          <StatusCard
            title="API Status"
            subtitle="FastAPI server health"
            status={status.api_online ? 'ok' : 'error'}
            icon={<ServerIcon size={18} />}
            value={<div>
              <div>Online: {String(status.api_online)}</div>
              <div>Uptime: {uptimeStr}</div>
            </div>}
          />
          <StatusCard
            title="Database"
            subtitle="Supabase connectivity"
            status={status.db_connected ? 'ok' : 'warn'}
            icon={<DatabaseIcon size={18} />}
            value={<div>
              <div>Connected: {String(status.db_connected)}</div>
              <div style={{ fontSize: 12, color: '#9ca3af' }}>{status.db_connected ? 'Cloud sync active' : 'Local-only mode'}</div>
            </div>}
          />
        </div>

        <div className="grid-2" style={{ gridTemplateColumns: '1fr 1fr' }}>
          <StatusCard
            title="Configuration"
            subtitle="Runtime settings"
            status={'none'}
            icon={<TimerIcon size={18} />}
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 13 }}>
              <div>Auto Update</div>
              <div style={{ color: '#aef' }}>{String(config.auto_update)}</div>
              <div>Voice Mode</div>
              <div style={{ color: '#aef' }}>{String(config.enable_voice_mode)}</div>
              <div>Cron Enabled</div>
              <div style={{ color: '#aef' }}>{String(config.cron_update_enabled)}</div>
              <div>Cron Expr</div>
              <div style={{ color: '#aef' }}>{String(config.cron_update_expression || '')}</div>
            </div>
          </StatusCard>
          <LogsPanel />
        </div>

        <div className="grid-2" style={{ gridTemplateColumns: '1fr 1fr' }}>
          <StatusCard title="Diagnostics" subtitle="Problems & anomalies" status={'none'} icon={<TimerIcon size={18} />}>
            <DiagnosticsPanel baseUrl="http://127.0.0.1:6060" />
          </StatusCard>
          <div className="neon-card" style={{ animation: 'none' }}>
            <div className="neon-card__title">Notes</div>
            <div style={{ fontSize: 13, color: '#9ca3af' }}>
              Diagnostics auto-refreshes every 15s. Use "Run Now" to force refresh.
            </div>
          </div>
        </div>
      </div>
      {error && <div className="status err">{error}</div>}
    </div>
  )
}