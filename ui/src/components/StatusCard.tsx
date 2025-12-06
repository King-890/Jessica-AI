import { ReactNode } from 'react'

type Status = 'ok' | 'warn' | 'error' | 'none'

export interface StatusCardProps {
  title: string
  subtitle?: string
  value?: string | number | ReactNode
  status?: Status
  icon?: ReactNode
  children?: ReactNode
  onClick?: () => void
}

const statusColor: Record<Status, string> = {
  ok: '#34d399',
  warn: '#f59e0b',
  error: '#ef4444',
  none: '#9ca3af',
}

export default function StatusCard({ title, subtitle, value, status = 'none', icon, children, onClick }: StatusCardProps) {
  return (
    <div
      className="neon-card"
      style={{
        background: 'linear-gradient(180deg, #0b1d2a 0%, #0b1220 100%)',
        borderColor: 'rgba(0, 229, 255, 0.6)',
        animation: 'drawerIn .2s ease-out',
      }}
      onClick={onClick}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {icon && <div style={{ color: '#aef' }}>{icon}</div>}
          <div>
            <div className="neon-card__title">{title}</div>
            {subtitle && <div style={{ color: '#9ca3af', fontSize: 12 }}>{subtitle}</div>}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: statusColor[status], boxShadow: '0 0 8px rgba(0,0,0,0.2)' }} />
        </div>
      </div>
      {value !== undefined && (
        <div style={{ marginTop: 10, fontSize: 16 }}>{value}</div>
      )}
      {children && (
        <div style={{ marginTop: 12 }}>{children}</div>
      )}
    </div>
  )
}