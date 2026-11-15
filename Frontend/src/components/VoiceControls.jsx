export default function VoiceControls({ isRecording, isSpeaking, disabled, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled}
      aria-pressed={isRecording}
      aria-label={isRecording ? 'Stop recording and send' : 'Start voice message'}
      className={`relative grid h-12 w-12 shrink-0 place-items-center rounded-full text-white transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal disabled:opacity-50 ${
        isRecording ? 'bg-dusk' : 'bg-teal hover:bg-deep'
      }`}
    >
      {isRecording && isSpeaking && (
        <span className="absolute inset-0 rounded-full bg-dusk/40 motion-safe:animate-ping" aria-hidden="true" />
      )}
      <svg viewBox="0 0 24 24" className="relative h-5 w-5" fill="currentColor" aria-hidden="true">
        {isRecording ? (
          <rect x="6" y="6" width="12" height="12" rx="2" />
        ) : (
          <path d="M12 15a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.9V22h2v-3.1A7 7 0 0 0 19 12h-2Z" />
        )}
      </svg>
    </button>
  )
}
