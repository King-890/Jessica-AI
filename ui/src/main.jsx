import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { ToastProvider } from './components/ToastProvider'
import { ErrorBoundaryWithToast } from './components/ErrorBoundary'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ToastProvider>
      <ErrorBoundaryWithToast>
        <App />
      </ErrorBoundaryWithToast>
    </ToastProvider>
  </StrictMode>,
)

// Inject Google CSE script once at app bootstrap
const CSE_ID = '570dcf594b44944f2'
function ensureCSE() {
  if (document.getElementById('gcse-script')) return
  const s = document.createElement('script')
  s.async = true
  s.id = 'gcse-script'
  s.src = `https://cse.google.com/cse.js?cx=${CSE_ID}`
  document.head.appendChild(s)
}
ensureCSE()
