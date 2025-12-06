import React from 'react'
import CodeEditor from '@/components/IDE/CodeEditor'
import Button from '@/components/Button'

export default function IDEWorkspace() {
  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div className="neon-card" style={{ animation: 'none' }}>
        <div className="neon-card__title">IDE Dashboard</div>
        <div style={{ display: 'flex', gap: 10 }}>
          <Button variant="neon">New File</Button>
          <Button variant="neon">Open Project</Button>
          <Button variant="neon">Share Session</Button>
        </div>
      </div>

      <CodeEditor />
    </div>
  )
}