import { useState } from 'react'
import ChatWindow from './components/ChatWindow'
import AudioPlayer from './components/AudioPlayer'
import useMicrophone from './hooks/useMicrophone'
import useSpeechDetection from './hooks/useSpeechDetection'
import useInterruptibleAudio from './hooks/useInterruptibleAudio'
import { sendMessage, sendVoice } from './services/chatApi'

let nextId = 1
const msg = (role, text, emergency = false) => ({ id: nextId++, role, text, emergency })

export default function App() {
  const [messages, setMessages] = useState([
    { id: 0, role: 'assistant', text: 'Hi, I’m MediVoice. This is a private space to talk about what’s on your mind. You can type or use the microphone.' },
  ])
  const [loading, setLoading] = useState(false)
  const mic = useMicrophone()
  const audio = useInterruptibleAudio()
  const { isSpeaking } = useSpeechDetection(mic.stream, { onSpeechStart: audio.stop })

  const push = (...m) => setMessages((prev) => [...prev, ...m])

  const handleReply = (res) => {
    push(msg('assistant', res.reply, res.is_emergency))
    if (res.audio_url) audio.play(res.audio_url)
  }

  const run = async (task) => {
    setLoading(true)
    try { await task() }
    catch (err) { push(msg('assistant', err?.message || 'I couldn’t reach the server. Check that the backend is running, then try again.')) }
    finally { setLoading(false) }
  }

  const onSend = (text) => {
    audio.stop()
    push(msg('user', text))
    run(async () => handleReply(await sendMessage(text)))
  }

  const toggleMic = async () => {
    if (!mic.isRecording) { audio.stop(); return mic.start() }
    const blob = await mic.stop()
    if (!blob) return
    run(async () => {
      const res = await sendVoice(blob)
      push(msg('user', res.transcript || 'Voice message'))
      handleReply(res)
    })
  }

  return (
    <div className="flex h-dvh flex-col">
      <header className="border-b border-teal/15 bg-white/70 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3">
          <div className="grid h-10 w-10 place-items-center rounded-full bg-deep font-semibold text-white" aria-hidden="true">M</div>
          <div>
            <h1 className="text-lg font-semibold leading-tight">MediVoice</h1>
            <p className="text-sm text-teal">{mic.isRecording ? 'Listening to you' : 'Here to listen'}</p>
          </div>
        </div>
      </header>

      <ChatWindow
        messages={messages}
        loading={loading}
        onSend={onSend}
        voice={{ isRecording: mic.isRecording, isSpeaking, onToggle: toggleMic }}
      />
      <AudioPlayer isPlaying={audio.isPlaying} onStop={audio.stop} />

      <footer className="px-4 pb-4 text-center text-xs text-ink/70">
        {mic.error && <p className="mb-1 text-amber" role="alert">{mic.error}</p>}
        MediVoice is not a doctor or a crisis service. In an emergency, call your local emergency number. In India, call Tele-MANAS at 14416.
      </footer>
    </div>
  )
}
