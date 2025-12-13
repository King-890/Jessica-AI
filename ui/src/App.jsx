import { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import './App.css'
import VoiceBubble from './components/VoiceBubble'
import VoiceStreamPanel from './components/VoiceStreamPanel'
import VoiceTranscribeTester from './components/VoiceTranscribeTester'
import MicWaveform from './components/MicWaveform'
import ChatPanel from './components/ChatPanel'
import CombinedSettings from './components/CombinedSettings'
import LiveLogs from './components/LiveLogs'
import KnowledgePanel from './components/KnowledgePanel'
import MemoryHistory from './components/MemoryHistory'
import VoiceControlPanel from './components/VoiceControlPanel'
import IntelligenceDashboard from './components/IntelligenceDashboard'
import Dashboard from '@/pages/Dashboard'
import IDEWorkspace from '@/pages/IDEWorkspace'
import TokenManager from './components/TokenManager'
import { activeTokenSource, isAuthRequired } from './utils/apiClient'
import { SupabaseAdapter, supabase } from './services/supabase'

const TABS = ['Home', 'Chat', 'Voice', 'Memory', 'Knowledge', 'Dashboard', 'IDE', 'Files', 'System', 'Terminal', 'Browser', 'Scheduler']

function App() {
  const [tab, setTab] = useState('Home')
  const [wsStatus, setWsStatus] = useState('disconnected')
  const wsRef = useRef(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [liveMode, setLiveMode] = useState(false)
  const [authSource, setAuthSource] = useState('none')
  const [authMsg, setAuthMsg] = useState('')

  const wsUrl = useMemo(() => 'ws://127.0.0.1:5050/ws', [])

  const connectWS = useCallback(() => {
    try {
      const ws = new WebSocket(wsUrl)
      ws.onopen = () => {
        setWsStatus('connected')
        // start heartbeat
        wsRef.current?.send(JSON.stringify({ type: 'heartbeat', payload: 'ping' }))
        // keepalive every 30s
        wsRef.current.__hb = setInterval(() => {
          try { wsRef.current?.send(JSON.stringify({ type: 'heartbeat', payload: 'ping' })) } catch (e) { void e }
        }, 30000)
      }
      ws.onclose = () => {
        setWsStatus('disconnected')
        if (wsRef.current?.__hb) clearInterval(wsRef.current.__hb)
      }
      ws.onerror = () => setWsStatus('error')
      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data)
          setMessages((prev) => [...prev, data])
        } catch (err) {
          setMessages((prev) => [...prev, { type: 'raw', message: ev.data }])
          console.debug('WS parse error', err)
        }
      }
      wsRef.current = ws
    } catch (err) {
      setWsStatus('error')
      console.debug('WS connect error', err)
    }
  }, [wsUrl])

  useEffect(() => {
    connectWS()
    return () => { try { wsRef.current?.close() } catch (err) { console.debug('WS close error', err) } }
  }, [connectWS])

  useEffect(() => {
    setAuthSource(activeTokenSource())
  }, [])

  async function signInWithSupabase() {
    try {
      // Use shared client directly


      const { data: { session }, error } = await supabase.auth.signInWithOAuth({ provider: 'github' })
      if (error) {
        setAuthMsg('OAuth failed')
        return
      }
      // Note: OAuth redirect will reload page. We need to handle session check on mount.
      // But for now keeping this logic
      if (session?.access_token) {
        setAuthSource('supabase')
        setAuthMsg('Signed in')
        setTimeout(() => setAuthMsg(''), 1500)
      }
    } catch (e) {
      setAuthMsg('Supabase error')
    }
  }




  // Subscription Effect
  useEffect(() => {
    let channel = null;
    if (authSource === 'supabase') {
      const convId = localStorage.getItem('supabase_conversation_id');
      if (convId) {
        console.log('Subscribing to chat:', convId);
        channel = SupabaseAdapter.subscribeToMessages(convId, (newMsg) => {
          // Avoid duplicating our own messages if we optimistically added them
          // Ideally we check ID, but for now just append
          if (newMsg.role === 'assistant') {
            setMessages(prev => [...prev, { type: 'chat', role: 'assistant', message: newMsg.content }]);
          }
        });
      }
    }
    return () => {
      if (channel) channel.unsubscribe();
    }
  }, [authSource])

  async function sendMessage() {
    const msg = input.trim()
    if (!msg) return

    setInput('') // Clear immediately for UX

    if (authSource === 'supabase') {
      // Supabase Mode
      setMessages((prev) => [...prev, { type: 'chat', input: msg, role: 'user' }]) // Optimistic update
      try {
        // Use a static conversation ID for demo, or generate one if missing
        let convId = localStorage.getItem('supabase_conversation_id');
        if (!convId) {
          convId = crypto.randomUUID();
          localStorage.setItem('supabase_conversation_id', convId);
        }

        await SupabaseAdapter.sendMessage(msg, convId);
        // Response and updates come via Subscription
      } catch (err) {
        console.error('Supabase send error', err);
        setAuthMsg('Send failed');
      }
    } else {
      // WebSocket Mode (Classic)
      try {
        wsRef.current?.send(JSON.stringify({ type: 'chat', payload: msg }))
        setMessages((prev) => [...prev, { type: 'chat', input: msg }])
      } catch (err) { console.debug('WS send error', err) }
    }
  }

  return (
    <div className="container">
      <div className="tabs">
        {TABS.map((t) => (
          <div key={t} className={`tab ${t === tab ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t}
          </div>
        ))}
      </div>

      <div className="content">
        <aside className="sidebar">
          <button className="btn" onClick={() => alert('Voice control coming soon')}>🎤 Voice Control</button>
          <button className="btn" onClick={() => alert('File manager coming soon')}>📁 File Manager</button>
          <button className="btn" onClick={() => setTab('Settings')}>⚙️ Settings Panel</button>
          <button className="btn" onClick={() => setTab('Browser')}>🔍 Search</button>
          <button className="btn" onClick={connectWS}>🔌 Connect WS</button>
        </aside>

        <main className="panel">
          <div className="panel-header">
            <h3>{tab}</h3>
            <span className={`status ${wsStatus === 'connected' ? 'ok' : wsStatus === 'error' ? 'err' : ''}`}>
              WS: {wsStatus}
            </span>
            <span style={{ marginLeft: 10 }} className="status">Live: {liveMode ? 'ON' : 'OFF'}</span>
            <span style={{ marginLeft: 10 }} className="status">
              {authSource === 'supabase' ? '🟢 Synced via Supabase' : authSource === 'dev' ? '🟡 Local API Token' : '🔴 Unauthenticated'}
            </span>
            {authMsg && <span style={{ marginLeft: 10 }} className="status">{authMsg}</span>}
            {authSource !== 'supabase' && (
              <button className="btn" style={{ marginLeft: 10 }} onClick={signInWithSupabase}>Sign in with Supabase</button>
            )}
          </div>

          {tab === 'Home' && (
            <div className="io">
              <div className="box">
                <div className="messages">
                  {messages.map((m, i) => (
                    <div key={i} className="msg">
                      <span className="label">{m.type}</span>
                      <span>{m.output || m.message || m.input || ''}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="box">
                <div className="input">
                  <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type a message" />
                  <button onClick={sendMessage}>Send</button>
                </div>
                <div style={{ marginTop: 10 }}>
                  <VoiceControlPanel backendUrl="http://127.0.0.1:6060" />
                </div>
              </div>
            </div>
          )}

          {tab === 'Files' && (
            <div className="io">
              <div className="box">
                <FilesPanel baseUrl="http://127.0.0.1:5050" />
              </div>
              <div className="box">
                <ProjectsPanel baseUrl="http://127.0.0.1:5050" />
              </div>
            </div>
          )}

          {tab === 'Terminal' && (
            <div className="io">
              <div className="box" style={{ gridColumn: '1 / -1' }}>
                <TerminalPanel baseUrl="http://127.0.0.1:5050" />
              </div>
            </div>
          )}

          {tab === 'Browser' && (
            <div className="box" style={{ gridColumn: '1 / -1' }}>
              <BrowserPanel baseUrl="http://127.0.0.1:5050" />
            </div>
          )}

          {tab === 'Memory' && (
            <div className="box" style={{ gridColumn: '1 / -1' }}>
              <MemoryHistory baseUrl="http://127.0.0.1:6060" />
            </div>
          )}

          {tab === 'Voice' && (
            <div className="io">
              <div className="box" style={{ gridColumn: '1 / -1' }}>
                <VoiceStreamPanel baseUrl="http://127.0.0.1:5050" />
              </div>
              <div className="box" style={{ gridColumn: '1 / -1', marginTop: 10 }}>
                <MicWaveform />
              </div>
              <div className="box" style={{ gridColumn: '1 / -1', marginTop: 10 }}>
                <VoiceTranscribeTester baseUrl="http://127.0.0.1:5050" />
              </div>
            </div>
          )}

          {tab === 'Chat' && (
            <div className="io">
              <div className="box" style={{ gridColumn: '1 / -1' }}>
                {activeTokenSource() !== 'supabase' && isAuthRequired() && <TokenManager />}
                <ChatPanel baseUrl="http://127.0.0.1:6060" />
              </div>
            </div>
          )}

          {tab === 'System' && (
            <div className="box" style={{ gridColumn: '1 / -1' }}>
              {activeTokenSource() !== 'supabase' && isAuthRequired() && <TokenManager />}
              <CombinedSettings backendUrl="http://127.0.0.1:6060" internalUrl="http://127.0.0.1:5050" />
            </div>
          )}
          {tab === 'System' && (
            <div className="box" style={{ gridColumn: '1 / -1', marginTop: 10 }}>
              <LiveLogs baseUrl="http://127.0.0.1:6060" />
            </div>
          )}

          {tab === 'Knowledge' && (
            <div className="box" style={{ gridColumn: '1 / -1' }}>
              <KnowledgePanel baseUrl="http://127.0.0.1:6060" />
            </div>
          )}

          {tab === 'Dashboard' && (
            <div className="box" style={{ gridColumn: '1 / -1' }}>
              <Dashboard />
            </div>
          )}

          {tab === 'IDE' && (
            <div className="box" style={{ gridColumn: '1 / -1' }}>
              <IDEWorkspace />
            </div>
          )}

          {tab === 'Scheduler' && (
            <div className="box" style={{ gridColumn: '1 / -1' }}>
              <SchedulerPanel baseUrl="http://127.0.0.1:5050" />
            </div>
          )}

          {tab !== 'Home' && tab !== 'Browser' && tab !== 'Scheduler' && tab !== 'System' && tab !== 'Memory' && tab !== 'Knowledge' && (
            <div className="box" style={{ gridColumn: '1 / -1' }}>
              <p>Section "{tab}" is a placeholder in Phase 1.</p>
            </div>
          )}

          <div style={{ marginTop: 10 }}>
            <small className="status">System tray integration planned for Tauri packaging.</small>
          </div>
        </main>
        <VoiceBubble
          wakeWord="jessica"
          live={liveMode}
          onWake={() => setLiveMode((v) => !v)}
          onTranscript={async (text) => {
            try {
              // Send to chat over WS
              wsRef.current?.send(JSON.stringify({ type: 'chat', payload: text }))
              setMessages((prev) => [...prev, { type: 'chat', input: text }])
            } catch (e) { void e }
            // Also trigger hands-free TTS on backend
            try {
              await fetch('http://127.0.0.1:5050/voice/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
              })
            } catch (e) { void e }
          }}
        />
      </div>
    </div>
  )
}

export default App

function FilesPanel({ baseUrl }) {
  const [path, setPath] = useState('workspace/main.py')
  const [content, setContent] = useState("print('Hello')")
  const [readOut, setReadOut] = useState('')

  async function createFile() {
    await fetch(`${baseUrl}/files/create`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path, content }) })
  }
  async function writeFile() {
    await fetch(`${baseUrl}/files/write`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path, content }) })
  }
  async function readFile() {
    const res = await fetch(`${baseUrl}/files/read?path=${encodeURIComponent(path)}`)
    const data = await res.json()
    setReadOut(data.content || '')
  }
  async function deleteFile() {
    await fetch(`${baseUrl}/files/delete`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path }) })
  }
  async function mkdir() {
    await fetch(`${baseUrl}/files/mkdir`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path }) })
  }

  return (
    <div>
      <h4>File Manager</h4>
      <div className="input">
        <input value={path} onChange={(e) => setPath(e.target.value)} placeholder="path" />
      </div>
      <div className="input">
        <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="content" rows={6} />
      </div>
      <div className="input">
        <button onClick={mkdir}>mkdir</button>
        <button onClick={createFile}>create</button>
        <button onClick={writeFile}>write</button>
        <button onClick={readFile}>read</button>
        <button onClick={deleteFile}>delete</button>
      </div>
      <pre className="messages" style={{ whiteSpace: 'pre-wrap' }}>{readOut}</pre>
    </div>
  )
}

function ProjectsPanel({ baseUrl }) {
  const [name, setName] = useState('MyApp')
  const [type, setType] = useState('python')
  const [result, setResult] = useState('')

  async function createProject() {
    const res = await fetch(`${baseUrl}/projects/create`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, type }) })
    const data = await res.json()
    setResult(JSON.stringify(data, null, 2))
  }

  return (
    <div>
      <h4>Project Scaffold</h4>
      <div className="input">
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="python">Python</option>
          <option value="flask">Flask</option>
          <option value="react">React</option>
          <option value="unity">Unity</option>
        </select>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Project Name" />
        <button onClick={createProject}>Create</button>
      </div>
      <pre className="messages" style={{ whiteSpace: 'pre-wrap' }}>{result}</pre>
    </div>
  )
}

function TerminalPanel({ baseUrl }) {
  const [command, setCommand] = useState('python')
  const [args, setArgs] = useState('workspace/main.py')
  const [out, setOut] = useState('')
  const [stream, setStream] = useState(false)
  const wsRef = useRef(null)

  async function run() {
    if (stream) {
      try {
        const ws = new WebSocket('ws://127.0.0.1:5050/ws/terminal')
        ws.onopen = () => {
          ws.send(JSON.stringify({ type: 'start', command, args: args.split(' ').filter(Boolean) }))
          setOut(`$ ${command} ${args}\n\n`)
        }
        ws.onmessage = (ev) => {
          try {
            const msg = JSON.parse(ev.data)
            if (msg.type === 'stdout') setOut((p) => p + msg.data)
            else if (msg.type === 'stderr') { setOut((p) => p + `\n[stderr]\n` + msg.data); voiceCue('warning', 'Command produced warnings.') }
            else if (msg.type === 'exit') { setOut((p) => p + `\n\n[exit ${msg.code}]`); voiceCue(msg.code === 0 ? 'success' : 'error', msg.code === 0 ? 'Command finished successfully' : 'Command failed') }
            else if (msg.type === 'error') { setOut((p) => p + `\n[error] ${msg.message}`); voiceCue('error', 'Command error occurred') }
          } catch (e) {
            setOut((p) => p + ev.data)
            void e
          }
        }
        ws.onerror = () => setOut((p) => p + '\n[ws error]')
        ws.onclose = () => { setOut((p) => p + '\n[ws closed]') }
        wsRef.current = ws
      } catch (e) {
        setOut(String(e))
      }
    } else {
      const res = await fetch(`${baseUrl}/system/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command, args: args.split(' ').filter(Boolean) }) })
      const data = await res.json()
      setOut(`$ ${command} ${args}\n\nSTDOUT:\n${data.stdout || ''}\n\nSTDERR:\n${data.stderr || ''}\n(Return code: ${data.returncode})`)
      try {
        const hasErr = Number(data.returncode) !== 0
        const hasWarn = !!data.stderr
        const context = hasErr ? 'error' : (hasWarn ? 'warning' : 'success')
        await voiceCue(context, hasErr ? 'Command failed' : hasWarn ? 'Command finished with warnings' : 'Command finished successfully')
      } catch (e) { void e }
    }
  }

  return (
    <div>
      <h4>Terminal</h4>
      <div className="input">
        <input value={command} onChange={(e) => setCommand(e.target.value)} placeholder="command" />
        <input value={args} onChange={(e) => setArgs(e.target.value)} placeholder="args (space-separated)" />
        <label style={{ marginLeft: 8 }}>
          <input type="checkbox" checked={stream} onChange={(e) => setStream(e.target.checked)} />
          Streaming
        </label>
        <button onClick={run}>Run</button>
      </div>
      <pre className="messages" style={{ whiteSpace: 'pre-wrap' }}>{out}</pre>
    </div>
  )
}

async function voiceCue(context, text) {
  try {
    if (typeof window !== 'undefined' && window.__voiceEventsEnabled === false) return
    await fetch('http://127.0.0.1:5050/voice/tts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, context }) })
  } catch (e) { void e }
}

function BrowserPanel({ baseUrl }) {
  const [q, setQ] = useState('fastapi websocket streaming example')
  const [results, setResults] = useState([])
  const [error, setError] = useState('')
  const [provider, setProvider] = useState('auto')

  async function search() {
    setError('')
    try {
      const res = await fetch(`${baseUrl}/search/web?q=${encodeURIComponent(q)}&num=5&provider=${encodeURIComponent(provider)}`)
      const data = await res.json()
      if (data.detail) {
        setError(data.detail)
        setResults([])
        return
      }
      setResults(data.results || [])
    } catch (e) {
      setError(String(e))
      setResults([])
    }
  }

  return (
    <div>
      <h4>Browser Search</h4>
      <div className="input">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search query" />
        <select value={provider} onChange={(e) => setProvider(e.target.value)} style={{ marginLeft: 8 }}>
          <option value="auto">auto</option>
          <option value="google">google</option>
          <option value="ddg">ddg</option>
        </select>
        <button onClick={search}>Search</button>
      </div>
      {error && <p className="status err">{error}</p>}
      <div className="messages">
        {results.map((r, i) => (
          <div key={i} className="msg">
            <a href={r.link} target="_blank" rel="noreferrer">{r.title}</a>
            <p>{r.snippet}</p>
            {r.provider && <small className="status ok">provider: {r.provider}</small>}
          </div>
        ))}
      </div>
    </div>
  )
}

function SchedulerPanel({ baseUrl }) {
  const [name, setName] = useState('Demo Task')
  const [command, setCommand] = useState('echo')
  const [args, setArgs] = useState('Hello World')
  const [scheduleType, setScheduleType] = useState('interval')
  const [intervalSeconds, setIntervalSeconds] = useState(60)
  const [cronExpr, setCronExpr] = useState('*/5 * * * *')
  const [isoTime, setIsoTime] = useState('')
  const [tasks, setTasks] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [results, setResults] = useState([])
  const [err, setErr] = useState('')

  const refresh = useCallback(async () => {
    const res = await fetch(`${baseUrl}/scheduler/list`)
    const data = await res.json()
    setTasks(data)
  }, [baseUrl])

  async function add() {
    setErr('')
    const payload = {
      name,
      command,
      args: args.split(' ').filter(Boolean),
      schedule_type: scheduleType,
      interval_seconds: scheduleType === 'interval' ? Number(intervalSeconds) : null,
      cron_expr: scheduleType === 'cron' ? cronExpr : null,
      iso_time: scheduleType === 'iso' ? isoTime : null,
      enabled: true,
    }
    const res = await fetch(`${baseUrl}/scheduler/add_advanced`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
    const data = await res.json()
    if (data.detail) setErr(data.detail)
    await refresh()
  }

  async function runNow(id) {
    await fetch(`${baseUrl}/scheduler/run_now`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) })
    await getResults(id)
  }

  async function toggle(id, enabled) {
    await fetch(`${baseUrl}/scheduler/enable`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id, enabled }) })
    await refresh()
  }

  async function getResults(id) {
    const res = await fetch(`${baseUrl}/scheduler/results?id=${id}`)
    const data = await res.json()
    setSelectedId(id)
    setResults(data)
    try {
      const last = Array.isArray(data) && data.length ? data[data.length - 1] : null
      if (last) {
        const hasErr = Number(last.returncode) !== 0
        const hasWarn = !!last.stderr
        const context = hasErr ? 'error' : (hasWarn ? 'warning' : 'success')
        await voiceCue(context, hasErr ? 'Task failed' : hasWarn ? 'Task finished with warnings' : 'Task finished successfully')
      }
    } catch (e) { void e }
  }

  useEffect(() => { refresh() }, [refresh])

  return (
    <div>
      <h4>Scheduler</h4>
      <div className="input">
        <select value={scheduleType} onChange={(e) => setScheduleType(e.target.value)}>
          <option value="interval">Interval</option>
          <option value="cron">Cron</option>
          <option value="iso">ISO</option>
        </select>
        {scheduleType === 'interval' && (
          <input type="number" value={intervalSeconds} onChange={(e) => setIntervalSeconds(e.target.value)} placeholder="seconds" />
        )}
        {scheduleType === 'cron' && (
          <input value={cronExpr} onChange={(e) => setCronExpr(e.target.value)} placeholder="cron expr" />
        )}
        {scheduleType === 'iso' && (
          <input value={isoTime} onChange={(e) => setIsoTime(e.target.value)} placeholder="YYYY-MM-DDTHH:mm:ssZ" />
        )}
      </div>
      <div className="input">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Task name" />
        <input value={command} onChange={(e) => setCommand(e.target.value)} placeholder="Command (python/echo/dir)" />
        <input value={args} onChange={(e) => setArgs(e.target.value)} placeholder="Args (space-separated)" />
        <button onClick={add}>Add</button>
      </div>
      {err && <p className="status err">{err}</p>}
      <div className="messages">
        {tasks.map((t) => (
          <div key={t.id} className="msg">
            <span className="label">#{t.id}</span>
            <strong>{t.name}</strong> — {t.command} {t.args.join(' ')}
            <small style={{ marginLeft: 8 }}>
              [{t.schedule_type}{t.schedule_type === 'interval' ? `:${t.interval_seconds}s` : t.schedule_type === 'cron' ? `:${t.cron_expr}` : t.schedule_type === 'iso' ? `:${t.iso_time}` : ''}] last: {t.last_run || 'never'}
            </small>
            <div style={{ marginTop: 6 }}>
              <button onClick={() => runNow(t.id)}>Run Now</button>
              <button onClick={() => toggle(t.id, !t.enabled)}>{t.enabled ? 'Disable' : 'Enable'}</button>
              <button onClick={() => getResults(t.id)}>Results</button>
            </div>
          </div>
        ))}
      </div>
      {selectedId && (
        <div style={{ marginTop: 10 }}>
          <h5>Results for Task #{selectedId}</h5>
          <div className="messages">
            {results.map((r) => (
              <div key={r.id} className="msg">
                <span className="label">{r.ts}</span>
                <pre style={{ whiteSpace: 'pre-wrap' }}>
                  {`Return: ${r.returncode}\nSTDOUT:\n${r.stdout || ''}\nSTDERR:\n${r.stderr || ''}`}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
// VoiceSettingsPanel replaced by CombinedSettings component
