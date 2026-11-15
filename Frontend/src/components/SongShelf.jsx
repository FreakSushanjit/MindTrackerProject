import { useState } from 'react'

const QUICK_MOODS = [
  { key: 'happy', label: 'Happy', icon: '😊', color: '#f59e0b' },
  { key: 'sad', label: 'Sad', icon: '😢', color: '#3b82f6' },
  { key: 'calm', label: 'Calm', icon: '😌', color: '#10b981' },
  { key: 'stressed', label: 'Stressed', icon: '💆', color: '#8b5cf6' },
  { key: 'excited', label: 'Excited', icon: '⚡', color: '#f97316' },
  { key: 'angry', label: 'Angry', icon: '🔥', color: '#ef4444' },
  { key: 'neutral', label: 'Neutral', icon: '🎧', color: '#6b7280' },
]

export default function SongShelf({ musicData, textEmotion, faceEmotion, onSelectMood, loadingMood }) {
  const [collapsed, setCollapsed] = useState(false)

  if (!musicData || !musicData.songs || musicData.songs.length === 0) {
    return null
  }

  const { songs, emotion_name, icon, description, color, mood_category } = musicData

  const openYoutube = (url, title, artist) => {
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer')
    } else {
      const q = encodeURIComponent(`${title} ${artist} bollywood`)
      window.open(`https://www.youtube.com/results?search_query=${q}`, '_blank')
    }
  }

  return (
    <section className="border-t border-teal/15 bg-white/95 px-4 py-3 shadow-lg backdrop-blur transition-all">
      <div className="mx-auto max-w-4xl">
        {/* Header bar with Emotion info & collapse toggle */}
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2">
          <div className="flex items-center gap-2">
            <span className="text-xl" aria-hidden="true">{icon || '🎵'}</span>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold tracking-tight text-ink">
                  Mood Suggestions: <span style={{ color }}>{emotion_name || mood_category}</span>
                </h3>
                {textEmotion && (
                  <span className="rounded-full bg-teal/10 px-2 py-0.5 text-[11px] font-semibold text-teal" title="Detected by DistilBERT Text Model">
                    Text: {textEmotion.emotion} ({Math.round((textEmotion.confidence || 0) * 100)}%)
                  </span>
                )}
                {faceEmotion && faceEmotion.face_detected && (
                  <span className="rounded-full bg-dusk/15 px-2 py-0.5 text-[11px] font-semibold text-dusk" title="Detected by DenseNet-121 Face Model">
                    Face: {faceEmotion.emotion} ({Math.round((faceEmotion.confidence || 0) * 100)}%)
                  </span>
                )}
              </div>
              <p className="text-xs text-ink/70">{description}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Quick Mood Selector Chips */}
            <div className="hidden sm:flex items-center gap-1">
              {QUICK_MOODS.map((m) => (
                <button
                  key={m.key}
                  onClick={() => onSelectMood && onSelectMood(m.key)}
                  className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium transition-all ${
                    mood_category === m.key
                      ? 'bg-deep text-white shadow-sm'
                      : 'bg-mist text-ink/80 hover:bg-teal/20'
                  }`}
                  title={`Browse ${m.label} songs`}
                >
                  <span>{m.icon}</span>
                  <span>{m.label}</span>
                </button>
              ))}
            </div>

            <button
              onClick={() => setCollapsed(!collapsed)}
              className="rounded-lg border border-teal/20 p-1 text-xs text-teal hover:bg-mist"
              aria-label={collapsed ? 'Expand music shelf' : 'Collapse music shelf'}
            >
              {collapsed ? '▲ Show Songs' : '▼ Hide'}
            </button>
          </div>
        </div>

        {/* Songs List */}
        {!collapsed && (
          <div className="mt-2">
            {loadingMood ? (
              <div className="py-6 text-center text-xs text-teal animate-pulse">Loading songs...</div>
            ) : (
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 md:grid-cols-3">
                {songs.map((song, idx) => (
                  <div
                    key={`${song.title}-${idx}`}
                    onClick={() => openYoutube(song.youtube_url, song.title, song.artist)}
                    className="group flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-teal/15 bg-white p-2.5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-teal/40 hover:shadow-md"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div
                        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-lg"
                        style={{ backgroundColor: `${color}20` }}
                      >
                        {song.icon || '🎶'}
                      </div>
                      <div className="min-w-0">
                        <h4 className="truncate text-xs font-semibold text-ink group-hover:text-deep">
                          {song.title}
                        </h4>
                        <p className="truncate text-[11px] text-ink/70">
                          {song.artist}
                        </p>
                        <div className="flex items-center gap-1.5 pt-0.5 text-[10px] text-teal">
                          {song.movie && <span className="truncate">🎬 {song.movie}</span>}
                          {song.bpm && <span className="rounded bg-mist px-1 py-0.2 font-mono">{song.bpm}</span>}
                        </div>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        openYoutube(song.youtube_url, song.title, song.artist)
                      }}
                      className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-deep text-[11px] text-white transition-transform group-hover:scale-110 group-hover:bg-teal"
                      title="Listen on YouTube"
                    >
                      ▶
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  )
}
