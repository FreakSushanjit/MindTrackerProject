import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'
import VoiceControls from './VoiceControls'

const STARTERS = ["I've been feeling anxious", 'I can’t sleep well', 'I need to talk']

export default function ChatWindow({ messages, loading, voice, onSend }) {
  const [text, setText] = useState('')
  const end = useRef(null)

  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])

  const submit = (e) => {
    e.preventDefault()
    const t = text.trim()
    if (!t || loading) return
    onSend(t)
    setText('')
  }

  return (
    <>
      <main className="flex-1 overflow-y-auto" aria-live="polite">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-3 px-4 py-6">
          {messages.map((m) => <MessageBubble key={m.id} {...m} />)}
          {loading && (
            <div className="flex w-fit gap-1 rounded-2xl rounded-bl-md bg-white px-4 py-3 shadow-sm" aria-label="MediVoice is typing">
              {[0, 150, 300].map((d) => (
                <span key={d} className="h-2 w-2 rounded-full bg-teal/60 motion-safe:animate-bounce" style={{ animationDelay: `${d}ms` }} />
              ))}
            </div>
          )}
          {messages.length === 1 && (
            <div className="flex flex-wrap gap-2 pt-2">
              {STARTERS.map((s) => (
                <button key={s} onClick={() => onSend(s)} className="rounded-full border border-teal/30 bg-white px-4 py-2 text-sm text-deep hover:border-teal focus-visible:outline-2 focus-visible:outline-teal">
                  {s}
                </button>
              ))}
            </div>
          )}
          <div ref={end} />
        </div>
      </main>

      <form onSubmit={submit} className="mx-auto flex w-full max-w-3xl items-end gap-2 px-4 pb-2">
        <textarea
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) submit(e) }}
          placeholder={voice.isRecording ? 'Listening…' : 'Type how you’re feeling'}
          aria-label="Message"
          className="max-h-32 min-h-12 flex-1 resize-none rounded-3xl border border-teal/20 bg-white px-5 py-3 text-[15px] outline-none focus:border-teal focus:ring-2 focus:ring-teal/20"
        />
        <VoiceControls {...voice} disabled={loading} />
        <button type="submit" disabled={!text.trim() || loading} className="h-12 shrink-0 rounded-full bg-deep px-5 font-medium text-white hover:bg-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal disabled:opacity-40">
          Send
        </button>
      </form>
    </>
  )
}
