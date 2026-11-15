import { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react'

const WebcamCapture = forwardRef(function WebcamCapture(
  { enabled, onDisable, lastFaceEmotion },
  ref
) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const [minimized, setMinimized] = useState(false)
  const [error, setError] = useState(null)
  const [isReady, setIsReady] = useState(false)

  // Expose captureFrame method to parent component via ref
  useImperativeHandle(ref, () => ({
    captureFrame: () => {
      if (!videoRef.current || !canvasRef.current || !isReady) {
        return null
      }
      try {
        const video = videoRef.current
        const canvas = canvasRef.current
        const width = video.videoWidth || 320
        const height = video.videoHeight || 240

        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')
        ctx.drawImage(video, 0, 0, width, height)

        // Return compressed JPEG data URL
        return canvas.toDataURL('image/jpeg', 0.8)
      } catch (err) {
        console.error('Failed to capture frame:', err)
        return null
      }
    },
    isReady: () => isReady,
  }))

  useEffect(() => {
    let active = true

    if (!enabled) {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
        streamRef.current = null
      }
      setIsReady(false)
      setError(null)
      return
    }

    async function startCamera() {
      try {
        setError(null)
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 320 },
            height: { ideal: 240 },
            facingMode: 'user',
          },
          audio: false,
        })

        if (!active) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }

        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.onloadedmetadata = () => {
            videoRef.current.play().catch(() => {})
            setIsReady(true)
          }
        }
      } catch (err) {
        console.error('Camera access error:', err)
        setError(err.name === 'NotAllowedError' ? 'Permission denied' : 'Camera unavailable')
        setIsReady(false)
      }
    }

    startCamera()

    return () => {
      active = false
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop())
        streamRef.current = null
      }
    }
  }, [enabled])

  if (!enabled) return null

  return (
    <div
      className={`fixed bottom-24 right-4 z-40 transition-all ${
        minimized ? 'w-48' : 'w-64'
      } rounded-2xl border border-teal/25 bg-white/95 p-2 shadow-2xl backdrop-blur`}
    >
      {/* Hidden canvas for capturing frame to base64 */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Top control bar */}
      <div className="flex items-center justify-between pb-1.5 px-1">
        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-teal opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-teal" />
          </span>
          <span className="text-[11px] font-semibold text-ink">Face Tracker</span>
        </div>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setMinimized(!minimized)}
            className="rounded p-1 text-xs text-ink/60 hover:bg-mist hover:text-ink"
            title={minimized ? 'Expand camera' : 'Minimize camera'}
          >
            {minimized ? '◻' : '─'}
          </button>
          <button
            type="button"
            onClick={onDisable}
            className="rounded p-1 text-xs text-red-500 hover:bg-mist"
            title="Turn off camera"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Video preview */}
      <div className="relative overflow-hidden rounded-xl bg-ink/90 aspect-4/3 flex items-center justify-center">
        {error ? (
          <div className="p-3 text-center text-xs text-amber-300">
            <p className="font-semibold">⚠️ {error}</p>
            <p className="mt-1 text-[10px] text-white/70">Check browser camera permissions</p>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              muted
              playsInline
              className="h-full w-full object-cover transform -scale-x-100"
            />
            {!isReady && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/40 text-xs text-white">
                Initializing...
              </div>
            )}
            {/* Live / Last emotion tag */}
            {lastFaceEmotion && (
              <div className="absolute bottom-1.5 left-1.5 right-1.5 rounded-lg bg-black/75 px-2 py-1 text-center text-[11px] font-semibold text-white backdrop-blur-xs">
                Face: {lastFaceEmotion.emotion || 'Neutral'}{' '}
                {lastFaceEmotion.confidence ? `(${Math.round(lastFaceEmotion.confidence * 100)}%)` : ''}
              </div>
            )}
          </>
        )}
      </div>

      <p className="mt-1.5 text-center text-[10px] text-ink/60">
        Frames analyzed when sending messages
      </p>
    </div>
  )
})

export default WebcamCapture
