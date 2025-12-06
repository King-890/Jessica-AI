import React from 'react'
import { useToast } from './ToastProvider'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  componentDidCatch(error, info) {
    try {
      // Toast within boundary is tricky; emit a custom event
      window.dispatchEvent(new CustomEvent('app:toast', { detail: { message: String(error), type: 'error' } }))
    } catch {}
    console.error('UI ErrorBoundary caught error:', error, info)
  }
  reset = () => this.setState({ hasError: false, error: null })
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 16 }}>
          <h3>Something went wrong</h3>
          <p style={{ color: '#b00' }}>{String(this.state.error || '')}</p>
          <button onClick={this.reset}>Reset</button>
        </div>
      )
    }
    return this.props.children
  }
}

export function ErrorBoundaryWithToast({ children }) {
  const { show } = useToast()
  React.useEffect(() => {
    const handler = (ev) => {
      const d = ev.detail || {}
      show(d.message || 'Error', d.type || 'error')
    }
    window.addEventListener('app:toast', handler)
    return () => window.removeEventListener('app:toast', handler)
  }, [show])
  return <ErrorBoundary>{children}</ErrorBoundary>
}