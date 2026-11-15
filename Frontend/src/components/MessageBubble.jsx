export default function MessageBubble({ role, text, emergency, text_emotion, face_emotion, dominant_emotion }) {
  const user = role === 'user'
  return (
    <div className={`flex ${user ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-[15px] leading-relaxed sm:max-w-[75%] ${
          user
            ? 'rounded-br-md bg-deep text-white shadow'
            : emergency
              ? 'rounded-bl-md border-2 border-amber bg-white shadow-sm'
              : 'rounded-bl-md bg-white shadow-sm border border-teal/10'
        }`}
      >
        {emergency && (
          <p className="mb-2 font-semibold text-amber">
            ⚠️ You may be in danger. Please contact emergency services or a crisis line now.
          </p>
        )}

        {/* Emotion Pills for assistant replies */}
        {!user && (text_emotion || face_emotion) && (
          <div className="mb-2 flex flex-wrap items-center gap-1.5 pb-1 border-b border-mist text-xs">
            {text_emotion && (
              <span className="inline-flex items-center gap-1 rounded-full bg-teal/10 px-2 py-0.5 text-[11px] font-medium text-teal">
                <span>💬</span>
                <span>Text Emotion: <strong>{text_emotion.emotion}</strong> ({Math.round((text_emotion.confidence || 0) * 100)}%)</span>
              </span>
            )}
            {face_emotion && face_emotion.face_detected && (
              <span className="inline-flex items-center gap-1 rounded-full bg-dusk/15 px-2 py-0.5 text-[11px] font-medium text-dusk">
                <span>📷</span>
                <span>Face Emotion: <strong>{face_emotion.emotion}</strong> ({Math.round((face_emotion.confidence || 0) * 100)}%)</span>
              </span>
            )}
          </div>
        )}

        <div>{text}</div>
      </div>
    </div>
  )
}
