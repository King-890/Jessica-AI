import { useEffect, useRef, useState } from 'react';

export default function VoiceBubble({ onTranscript, wakeWord = 'jessica', live = false, onWake }) {
  const [listening, setListening] = useState(false);
  const [theme, setTheme] = useState('light');
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

    async function startListening() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        alert('SpeechRecognition not supported in this browser');
        return;
      }
      const sr = new SpeechRecognition();
      sr.lang = 'en-US';
      sr.continuous = true;
      sr.interimResults = true;
      sr.onresult = (e) => {
        let text = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
          text += e.results[i][0].transcript;
        }
        const lower = text.toLowerCase();
        const ww = String(wakeWord || '').toLowerCase();
        if (ww && lower.includes(ww)) {
          onWake && onWake();
          const cleaned = text.replace(new RegExp(wakeWord, 'i'), '').trim();
          if (cleaned) onTranscript && onTranscript(cleaned);
        } else if (live) {
          onTranscript && onTranscript(text);
        }
      };
      sr.onerror = () => { setListening(false); };
      sr.onend = () => { setListening(false); };
      sr.start();
      setListening(true);

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        audioCtxRef.current = audioCtx;
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        analyserRef.current = analyser;
        source.connect(analyser);
        drawWaveform();
      } catch (e) {
        void e
      }
    }

  function stopListening() {
    setListening(false);
    const ctx = audioCtxRef.current;
    if (ctx) ctx.close();
  }

  function drawWaveform() {
    const analyser = analyserRef.current;
    const canvas = canvasRef.current;
    if (!analyser || !canvas) return;
    const ctx = canvas.getContext('2d');
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    function draw() {
      requestAnimationFrame(draw);
      analyser.getByteTimeDomainData(dataArray);
      ctx.fillStyle = 'rgba(0,0,0,0)';
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.lineWidth = 2;
      ctx.strokeStyle = theme === 'dark' ? '#00e5ff' : '#0077cc';
      ctx.beginPath();
      const sliceWidth = canvas.width * 1.0 / bufferLength;
      let x = 0;
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = v * canvas.height / 2;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }
      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();
    }
    draw();
  }

  return (
    <div style={{ position: 'fixed', bottom: 20, right: 20, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
      <canvas ref={canvasRef} width={120} height={40} style={{ background: 'transparent' }} />
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={() => listening ? stopListening() : startListening()}>
          {listening ? 'Stop' : 'Hey Jessica'}
        </button>
        <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
          {theme === 'dark' ? 'Light' : 'Dark'}
        </button>
        <span style={{ fontSize: 12, alignSelf: 'center' }}>
          {live ? 'Live: ON' : 'Live: OFF'}
        </span>
      </div>
    </div>
  );
}