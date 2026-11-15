import { useState, useRef, useEffect } from 'react'
import ChatWindow from './components/ChatWindow'
import AudioPlayer from './components/AudioPlayer'
import SongShelf from './components/SongShelf'
import CameraConsentModal from './components/CameraConsentModal'
import WebcamCapture from './components/WebcamCapture'
import useMicrophone from './hooks/useMicrophone'
import useSpeechDetection from './hooks/useSpeechDetection'
import useInterruptibleAudio from './hooks/useInterruptibleAudio'
import { sendMessage, sendVoice, fetchSongsByMood } from './services/chatApi'

let nextId = 1
const msg = (role, text, emergency = false, extra = {}) => ({
  id: nextId++,
  role,
  text,
  emergency,
  ...extra,
})

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: 0,
      role: 'assistant',
      text: 'Hi, I’m MediVoice MindTracker. I analyze your emotional state through your words (and optionally your camera) to provide personalized, context-aware support and mood-based music recommendations.',
    },
  ])
  const [loading, setLoading] = useState(false)
  const [cameraEnabled, setCameraEnabled] = useState(false)
  const [showConsentModal, setShowConsentModal] = useState(false)
  const [latestMusic, setLatestMusic] = useState(null)
  const [lastTextEmotion, setLastTextEmotion] = useState(null)
  const [lastFaceEmotion, setLastFaceEmotion] = useState(null)
  const [loadingMood, setLoadingMood] = useState(false)

  const mic = useMicrophone()
  const audio = useInterruptibleAudio()
  const webcamRef = useRef(null)
  const { isSpeaking } = useSpeechDetection(mic.stream, { onSpeechStart: audio.stop })

  const push = (...m) => setMessages((prev) => [...prev, ...m])

  // Fetch initial calm playlist on mount
  useEffect(() => {
    fetchSongsByMood('calm')
      .then((data) => setLatestMusic(data))
      .catch((err) => console.log('Initial music load notice:', err))
  }, [])

  const handleReply = (res) => {
    push(
      msg('assistant', res.reply, res.is_emergency, {
        text_emotion: res.text_emotion,
        face_emotion: res.face_emotion,
        dominant_emotion: res.dominant_emotion,
      })
    )

    if (res.music) {
      setLatestMusic(res.music)
    }
    if (res.text_emotion) {
      setLastTextEmotion(res.text_emotion)
    }
    if (res.face_emotion) {
      setLastFaceEmotion(res.face_emotion)
    }
    if (res.audio_url) {
      audio.play(res.audio_url)
    }
  }

  const run = async (task) => {
    setLoading(true)
    try {
      await task()
    } catch (err) {
      push(
        msg(
          'assistant',
          err?.message ||
            'I couldn’t reach the server. Please ensure the backend is running and try again.'
        )
      )
    } finally {
      setLoading(false)
    }
  }

  const onSend = (text) => {
    audio.stop()
    push(msg('user', text))

    // Capture webcam frame if enabled
    let faceImage = null
    if (cameraEnabled && webcamRef.current) {
      faceImage = webcamRef.current.captureFrame()
    }

    run(async () => {
      const res = await sendMessage(text, { faceImage, cameraEnabled })
      handleReply(res)
    })
  }

  const toggleMic = async () => {
    if (!mic.isRecording) {
      audio.stop()
      return mic.start()
    }
    const blob = await mic.stop()
    if (!blob) return
    run(async () => {
      const res = await sendVoice(blob)
      push(msg('user', res.transcript || 'Voice message'))
      handleReply(res)
    })
  }

  const handleToggleCamera = () => {
    if (!cameraEnabled) {
      // Prompt user for consent first
      setShowConsentModal(true)
    } else {
      setCameraEnabled(false)
    }
  }

  const handleConfirmCamera = () => {
    setShowConsentModal(false)
    setCameraEnabled(true)
  }

  const handleCancelCamera = () => {
    setShowConsentModal(false)
  }

  const handleSelectMood = async (mood) => {
    setLoadingMood(true)
    try {
      const data = await fetchSongsByMood(mood)
      setLatestMusic(data)
    } catch (err) {
      console.error('Failed to load songs for mood:', mood, err)
    } finally {
      setLoadingMood(false)
    }
  }

  return (
    <div className="flex h-dvh flex-col bg-mist">
      {/* Header */}
      <header className="border-b border-teal/15 bg-white/80 shadow-xs backdrop-blur-md">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div
              className="grid h-10 w-10 place-items-center rounded-full bg-deep font-bold text-white shadow-sm"
              aria-hidden="true"
            >
              M
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold leading-tight text-ink">
                  MediVoice MindTracker
                </h1>
                <span className="rounded-full bg-teal/15 px-2 py-0.5 text-[10px] font-semibold text-teal uppercase tracking-wider">
                  AI + Emotion
                </span>
              </div>
              <p className="text-xs text-teal">
                {mic.isRecording
                  ? '🎙️ Listening to you...'
                  : cameraEnabled
                  ? '📷 Camera active • Face + Text Emotion tracking'
                  : 'Here to listen and support'}
              </p>
            </div>
          </div>

          {/* Quick Header Controls */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleToggleCamera}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-all shadow-xs ${
                cameraEnabled
                  ? 'bg-teal text-white ring-2 ring-teal/30'
                  : 'border border-teal/25 bg-white text-ink/80 hover:bg-mist hover:text-teal'
              }`}
            >
              <span>📷</span>
              <span>{cameraEnabled ? 'Camera On' : 'Use Camera'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Chat Interface */}
      <ChatWindow
        messages={messages}
        loading={loading}
        onSend={onSend}
        voice={{ isRecording: mic.isRecording, isSpeaking, onToggle: toggleMic }}
        camera={{ enabled: cameraEnabled, onToggle: handleToggleCamera }}
      />

      {/* Music Suggestions Shelf at the Bottom */}
      <SongShelf
        musicData={latestMusic}
        textEmotion={lastTextEmotion}
        faceEmotion={lastFaceEmotion}
        onSelectMood={handleSelectMood}
        loadingMood={loadingMood}
      />

      {/* Floating Webcam Tracker Component */}
      <WebcamCapture
        ref={webcamRef}
        enabled={cameraEnabled}
        onDisable={() => setCameraEnabled(false)}
        lastFaceEmotion={lastFaceEmotion}
      />

      {/* Camera Permission & Privacy Consent Modal */}
      <CameraConsentModal
        isOpen={showConsentModal}
        onConfirm={handleConfirmCamera}
        onCancel={handleCancelCamera}
      />

      <AudioPlayer isPlaying={audio.isPlaying} onStop={audio.stop} />

      <footer className="px-4 pb-2 pt-1 text-center text-[11px] text-ink/60 bg-white/50 border-t border-teal/10">
        {mic.error && <p className="mb-1 text-amber font-medium" role="alert">{mic.error}</p>}
        MediVoice is an AI wellness assistant and not a medical doctor. In emergencies, please contact local emergency services or Tele-MANAS (14416).
      </footer>
    </div>
  )
}
