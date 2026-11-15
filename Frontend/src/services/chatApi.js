// Expected backend contract (adjust to match app/api/chat.py and voice.py):
//   POST /api/chat   { message }        -> { reply, is_emergency, audio_url? }
//   POST /api/voice  multipart "audio"  -> { transcript, reply, is_emergency, audio_url? }
const BASE = '/api'

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    let msg = `Request failed (${res.status})`
    try {
      const data = await res.json()
      if (data?.detail) msg = data.detail
    } catch {
      // fallback to generic message
    }
    throw new Error(msg)
  }
  return res.json()
}

export const sendMessage = (message) =>
  request('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })

export const sendVoice = (blob) => {
  const body = new FormData()
  body.append('audio', blob, 'recording.webm')
  return request('/voice', { method: 'POST', body })
}
