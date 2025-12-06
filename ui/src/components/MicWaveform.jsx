import { useEffect, useRef, useState } from 'react'

export default function MicWaveform() {
  const canvasRef = useRef(null)
  const [active, setActive] = useState(false)
  const audioRef = useRef({})

  useEffect(() => {
    return () => {
      try { audioRef.current.stream?.getTracks()?.forEach((t) => t.stop()) } catch {}
      try { audioRef.current.ctx?.close() } catch {}
    }
  }, [])

  async function start() {
    if (active) return
    setActive(true)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const ctx = new (window.AudioContext || window.webkitAudioContext)()
      const src = ctx.createMediaStreamSource(stream)
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 1024
      src.connect(analyser)
      audioRef.current = { stream, ctx, analyser }
      draw()
    } catch (e) {
      setActive(false)
      console.error('MicWaveform start error', e)
    }
  }

  function stop() {
    setActive(false)
    try { audioRef.current.stream?.getTracks()?.forEach((t) => t.stop()) } catch {}
    try { audioRef.current.ctx?.close() } catch {}
  }

  function draw() {
    const canvas = canvasRef.current
    if (!canvas || !audioRef.current.analyser) return
    const ctx2d = canvas.getContext('2d')
    const bufferLength = audioRef.current.analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)
    function loop() {
      if (!active) return
      audioRef.current.analyser.getByteTimeDomainData(dataArray)
      ctx2d.clearRect(0, 0, canvas.width, canvas.height)
      ctx2d.beginPath()
      const slice = canvas.width / bufferLength
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0
        const y = (v * canvas.height) / 2
        const x = i * slice
        if (i === 0) ctx2d.moveTo(x, y)
        else ctx2d.lineTo(x, y)
      }
      ctx2d.strokeStyle = '#0b6'
      ctx2d.lineWidth = 2
      ctx2d.stroke()
      requestAnimationFrame(loop)
    }
    loop()
  }

  return (
    <div>
      <h4>Mic Waveform</h4>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <button onClick={start} disabled={active}>Start</button>
        <button onClick={stop} disabled={!active}>Stop</button>
      </div>
      <canvas ref={canvasRef} width={600} height={120} style={{ border: '1px solid #ddd', marginTop: 8 }} />
    </div>
  )
}