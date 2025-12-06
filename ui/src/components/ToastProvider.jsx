import { createContext, useContext, useState, useCallback } from 'react'

const ToastCtx = createContext({ show: () => {} })

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const show = useCallback((message, type = 'info', ttl = 2500) => {
    const id = Math.random().toString(36).slice(2)
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), ttl)
  }, [])

  return (
    <ToastCtx.Provider value={{ show }}>
      {children}
      <div style={{ position: 'fixed', right: 12, bottom: 12, display: 'flex', flexDirection: 'column', gap: 8, zIndex: 9999 }}>
        {toasts.map((t) => (
          <div key={t.id} style={{ background: t.type === 'error' ? '#ffdddd' : t.type === 'success' ? '#ddffdd' : '#eef', border: '1px solid #ccc', borderRadius: 6, padding: '8px 10px', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}>
            <strong style={{ marginRight: 6 }}>{t.type}</strong>
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  )
}

export function useToast() {
  return useContext(ToastCtx)
}