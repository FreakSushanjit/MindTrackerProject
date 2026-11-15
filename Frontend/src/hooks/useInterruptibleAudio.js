import { useCallback, useEffect, useRef, useState } from 'react'

export default function useInterruptibleAudio() {
  const ref = useRef(null)
  const [isPlaying, setIsPlaying] = useState(false)

  const stop = useCallback(() => {
    ref.current?.pause()
    ref.current = null
    setIsPlaying(false)
  }, [])

  const play = useCallback((url) => {
    stop()
    const a = new Audio(url)
    ref.current = a
    a.onended = a.onerror = () => setIsPlaying(false)
    a.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false))
  }, [stop])

  useEffect(() => stop, [stop])

  return { isPlaying, play, stop }
}
