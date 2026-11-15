import { useCallback, useRef, useState } from 'react'

export default function useMicrophone() {
  const [stream, setStream] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState(null)
  const recorder = useRef(null)
  const chunks = useRef([])

  const start = useCallback(async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      })
      const r = new MediaRecorder(s)
      chunks.current = []
      r.ondataavailable = (e) => e.data.size && chunks.current.push(e.data)
      r.start()
      recorder.current = r
      setStream(s)
      setIsRecording(true)
      setError(null)
    } catch {
      setError('Microphone is blocked. Allow access in your browser settings.')
    }
  }, [])

  // Resolves with the recorded audio Blob
  const stop = useCallback(
    () =>
      new Promise((resolve) => {
        const r = recorder.current
        if (!r) return resolve(null)
        r.onstop = () => {
          r.stream.getTracks().forEach((t) => t.stop())
          setStream(null)
          setIsRecording(false)
          resolve(new Blob(chunks.current, { type: r.mimeType }))
        }
        r.stop()
      }),
    [],
  )

  return { stream, isRecording, error, start, stop }
}
