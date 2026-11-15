export default function MessageBubble({ role, text, emergency }) {
  const user = role === 'user'
  return (
    <div className={`flex ${user ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-[15px] leading-relaxed sm:max-w-[75%] ${
          user
            ? 'rounded-br-md bg-deep text-white'
            : emergency
              ? 'rounded-bl-md border-2 border-amber bg-white'
              : 'rounded-bl-md bg-white shadow-sm'
        }`}
      >
        {emergency && (
          <p className="mb-1 font-semibold text-amber">
            You may be in danger. Please contact emergency services or a crisis line now.
          </p>
        )}
        {text}
      </div>
    </div>
  )
}
