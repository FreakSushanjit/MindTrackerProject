export default function AudioPlayer({ isPlaying, onStop }) {
  if (!isPlaying) return null
  return (
    <div className="mx-auto flex w-full max-w-3xl items-center justify-between gap-3 px-4 pb-2" role="status">
      <span className="flex items-center gap-2 text-sm text-teal">
        <span className="flex items-end gap-0.5" aria-hidden="true">
          {[0, 150, 300].map((d) => (
            <span key={d} className="h-3 w-1 rounded bg-teal motion-safe:animate-bounce" style={{ animationDelay: `${d}ms` }} />
          ))}
        </span>
        Reading reply aloud. Speak to interrupt.
      </span>
      <button onClick={onStop} className="rounded-full px-3 py-1 text-sm font-medium text-deep hover:bg-white focus-visible:outline-2 focus-visible:outline-teal">
        Stop
      </button>
    </div>
  )
}
