import React from 'react'

type Props = {
  children: React.ReactNode
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void
  variant?: 'neon' | 'primary' | 'ghost'
  iconOnly?: boolean
  title?: string
  style?: React.CSSProperties
}

export default function Button({ children, onClick, variant = 'neon', iconOnly = false, title, style }: Props) {
  const cls = variant === 'neon'
    ? `neon-button${iconOnly ? ' icon-only' : ''}`
    : variant === 'primary'
      ? 'big-button'
      : 'btn'
  return (
    <button className={cls} title={title} onClick={onClick} style={style}>
      {children}
    </button>
  )
}