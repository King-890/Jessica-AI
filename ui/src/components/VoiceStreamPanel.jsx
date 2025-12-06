import { useEffect, useRef, useState, useCallback } from 'react'

// Streams microphone audio as PCM16 mono 16kHz over WebSocket to /voice/stt_ws
export default function VoiceStreamPanel({ baseUrl = 'http://127.0.0.1:5050' }) {
  const [listening, setListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [bytesSent, setBytesSent] = useState(0)
  const [err, setErr] = useState('')
  const audioCtxRef = useRef(null)
  const procRef = useRef(null)
  const wsRef = useRef(null)
  const streamRef = useRef(null)

  const start = useCallback(async () => {
    setErr('')
    setTranscript('')
    setBytesSent(0)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1 } })
      streamRef.current = stream
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      const audioCtx = new AudioCtx()
      audioCtxRef.current = audioCtx
      const source = audioCtx.createMediaStreamSource(stream)
      const processor = audioCtx.createScriptProcessor(4096, 1, 1)
      procRef.current = processor

      const ws = new WebSocket(baseUrl.replace('http', 'ws') + '/voice/stt_ws')
      ws.onopen = () => {
        setListening(true)
        source.connect(processor)
        processor.connect(audioCtx.destination)
      }
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data)
          if (msg.type === 'final') setTranscript(msg.text || '')
          else if (msg.type === 'partial') setTranscript(msg.text || '')
          else if (msg.type === 'progress') setBytesSent(msg.bytes || 0)
        } catch (e) { void e }
      }
      ws.onerror = () => { setErr('WebSocket error'); stop(true) }
      ws.onclose = () => { setListening(false) }
      wsRef.current = ws

      const inputRate = audioCtx.sampleRate
      const targetRate = 16000

      function downsample(buffer) {
        const ratio = inputRate / targetRate
        const newLen = Math.round(buffer.length / ratio)
        const result = new Float32Array(newLen)
        let offsetResult = 0
        let offsetBuffer = 0
        while (offsetResult < result.length) {
          const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio)
          let accum = 0
          let count = 0
          for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
            accum += buffer[i]
            count++
          }
          result[offsetResult] = accum / (count || 1)
          offsetResult++
          offsetBuffer = nextOffsetBuffer
        }
        return result
      }

      function floatTo16BitPCM(float32Array) {
        const out = new Int16Array(float32Array.length)
        for (let i = 0; i < float32Array.length; i++) {
          let s = Math.max(-1, Math.min(1, float32Array[i]))
          out[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
        }
        return out
      }

      processor.onaudioprocess = (e) => {
        try {
          const input = e.inputBuffer.getChannelData(0)
          const down = downsample(input)
          const pcm16 = floatTo16BitPCM(down)
          wsRef.current?.send(pcm16.buffer)
          setBytesSent((b) => b + pcm16.byteLength)
        } catch (e) { void e }
      }
    } catch (e) {
      setErr(String(e))
      stop(true)
    }
  }, [baseUrl, stop])

  const stop = useCallback(async (silent = false) => {
    try {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && !silent) {
        wsRef.current.send('finish')
      }
    } catch (e) { void e }
    try { procRef.current && procRef.current.disconnect() } catch (e) { void e }
    try { audioCtxRef.current && audioCtxRef.current.close() } catch (e) { void e }
    try { streamRef.current && streamRef.current.getTracks().forEach(t => t.stop()) } catch (e) { void e }
    try { wsRef.current && wsRef.current.close() } catch (e) { void e }
    setListening(false)
  }, [])

  useEffect(() => () => { stop(true) }, [stop])

  return (
    <div>
      <h4>Voice Streaming (WebSocket)</h4>
      <div className="input" style={{ alignItems: 'center' }}>
        <button onClick={() => listening ? stop() : start()}>{listening ? 'Stop' : 'Start'}</button>
        <span className="status" style={{ marginLeft: 8 }}>Bytes: {bytesSent}</span>
      </div>
      {err && <p className="status err">{err}</p>}
      <div className="messages">
        <div className="msg">
          <span className="label">transcript</span>
          <span>{transcript}</span>
        </div>
      </div>
    </div>
  )
}