import { useEffect, useRef, useState } from 'react'

// Watches a mic stream and reports when the user starts talking.
export default function useSpeechDetection(stream, { threshold = 0.05, onSpeechStart } = {}) {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const cb = useRef(onSpeechStart)
  cb.current = onSpeechStart

  useEffect(() => {
    if (!stream) return setIsSpeaking(false)
    const ctx = new AudioContext()
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 512
    ctx.createMediaStreamSource(stream).connect(analyser)
    const data = new Uint8Array(analyser.fftSize)
    let raf, speaking = false, quietSince = 0

    const tick = (now) => {
      analyser.getByteTimeDomainData(data)
      let sum = 0
      for (const v of data) sum += ((v - 128) / 128) ** 2
      const loud = Math.sqrt(sum / data.length) > threshold
      if (loud) {
        quietSince = now
        if (!speaking) { speaking = true; setIsSpeaking(true); cb.current?.() }
      } else if (speaking && now - quietSince > 700) {
        speaking = false
        setIsSpeaking(false)
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => { cancelAnimationFrame(raf); ctx.close() }
  }, [stream, threshold])

  return { isSpeaking }
}
