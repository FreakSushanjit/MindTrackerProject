export default function CameraConsentModal({ isOpen, onConfirm, onCancel }) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs animate-fade-in">
      <div className="w-full max-w-md rounded-2xl border border-teal/20 bg-white p-6 shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="grid h-12 w-12 place-items-center rounded-full bg-teal/15 text-2xl text-teal" aria-hidden="true">
            📷
          </div>
          <div>
            <h2 className="text-lg font-bold text-ink">Enable Facial Emotion Detection?</h2>
            <p className="text-xs text-teal font-medium">Enhanced Context-Aware Empathy</p>
          </div>
        </div>

        <p className="mt-4 text-sm leading-relaxed text-ink/80">
          If you agree, MediVoice will use your webcam to detect facial expressions (e.g. happiness, stress, sadness, anxiety) alongside your written text.
        </p>

        <div className="mt-3 rounded-xl bg-mist/60 p-3 text-xs text-ink/70">
          <ul className="space-y-1 list-disc list-inside">
            <li>Your camera feed is analyzed in real-time to personalize the assistant’s guidance.</li>
            <li>No video or images are stored, recorded, or shared with third parties.</li>
            <li>You can disable the camera anytime with a single click.</li>
          </ul>
        </div>

        <div className="mt-6 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl border border-teal/30 px-4 py-2.5 text-sm font-medium text-ink hover:bg-mist transition-colors"
          >
            No, Thanks
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded-xl bg-deep px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-teal transition-all"
          >
            Agree &amp; Enable Camera
          </button>
        </div>
      </div>
    </div>
  )
}
