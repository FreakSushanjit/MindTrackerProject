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

export const sendMessage = (message, { faceImage = null, cameraEnabled = false } = {}) =>
  request('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      face_image: faceImage,
      camera_enabled: cameraEnabled,
    }),
  })

export const sendVoice = (blob) => {
  const body = new FormData()
  body.append('audio', blob, 'recording.webm')
  return request('/voice', { method: 'POST', body })
}

export const detectFace = (imageBase64) =>
  request('/detect-face', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image: imageBase64 }),
  })

export const fetchSongsByMood = (mood = 'calm', limit = 6) =>
  request(`/songs?mood=${encodeURIComponent(mood)}&limit=${limit}`, {
    method: 'GET',
  })
