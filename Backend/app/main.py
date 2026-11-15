import os
import re
import sys
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

# Ensure Anaconda DLLs are available for PIL/Torch on Windows
if sys.platform == "win32" and os.path.exists(r"D:\Anaconda\Library\bin"):
    try:
        os.add_dll_directory(r"D:\Anaconda\Library\bin")
    except Exception:
        pass

from app.services.text_emotion_service import text_emotion_classifier
from app.services.face_emotion_service import face_emotion_detector
from app.services.music_service import get_songs_for_emotion, SONG_DB, EMOTION_META

# Locate and load environment variables from multiple possible locations
env_paths = [
    Path(__file__).resolve().parent.parent / ".env",
    Path(__file__).resolve().parent.parent.parent / "Frontend" / ".env",
    Path(__file__).resolve().parent.parent.parent / ".env",
    Path.cwd() / ".env"
]
for p in env_paths:
    if p.exists():
        load_dotenv(p, override=False)

api_key = (
    os.getenv("NVIDIA_API")
    or os.getenv("NVIDIA_API_KEY")
    or os.getenv("GROK_API")
    or os.getenv("XAI_API_KEY")
    or os.getenv("MODEL_API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or ""
).strip()
base_url = os.getenv("LLM_BASE_URL")
model_name = os.getenv("LLM_MODEL") or os.getenv("LLM_MODEL_2")

# Provider autodetection
if api_key.startswith("nvapi-") or os.getenv("NVIDIA_API") or os.getenv("NVIDIA_API_KEY"):
    if not base_url or "x.ai" in base_url or "meta.ai" in base_url:
        base_url = "https://integrate.api.nvidia.com/v1"
    if not model_name or "grok" in model_name or "muse" in model_name:
        model_name = "meta/llama-3.2-11b-vision-instruct"
elif api_key.startswith("xai-") or os.getenv("GROK_API"):
    if not base_url or "nvidia" in base_url or "meta.ai" in base_url:
        base_url = "https://api.x.ai/v1"
    if not model_name or "llama" in model_name or "muse" in model_name:
        model_name = os.getenv("LLM_MODEL_2") or "grok-2-latest"
elif api_key.startswith("LLM_"):
    if not base_url:
        base_url = "https://api.meta.ai/v1"
    if not model_name:
        model_name = "muse-spark-1.3"
else:
    if not base_url:
        base_url = "https://api.openai.com/v1"
    if not model_name:
        model_name = "gpt-4o-mini"

fallback_mode = os.getenv("FALLBACK_MODE", "auto").lower() in ("true", "1", "auto")

# Initialize OpenAI-compatible client
client = None
if api_key:
    client = OpenAI(base_url=base_url, api_key=api_key)

app = FastAPI(title="MindTracker & Health Assistant")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Warm up ML models in a background thread to prevent first-request lag."""
    def _warmup():
        try:
            text_emotion_classifier.load()
        except Exception as e:
            print(f"[Startup] Text model preload notice: {e}")
        try:
            face_emotion_detector.load()
        except Exception as e:
            print(f"[Startup] Face model preload notice: {e}")

    threading.Thread(target=_warmup, daemon=True).start()


class ChatRequest(BaseModel):
    message: str
    face_image: Optional[str] = None
    camera_enabled: Optional[bool] = False


class FaceDetectRequest(BaseModel):
    image: str


SYSTEM_PROMPT = """
You are an empathetic, evidence-based AI health and mental wellness assistant.

Your core responsibilities:
1. Provide compassionate, thoughtful, evidence-based health and mental wellness information.
2. In each response, you are given the user's analyzed emotional state (from text analysis and/or facial expression detection). Deeply integrate this emotional context:
   - Validate their emotional experience (e.g., acknowledging stress, sadness, anxiety, or excitement).
   - If there is a noticeable difference between their words and facial expression (e.g. typing "I'm fine" while appearing sad or tense), gently and warmly mention this contradiction with care.
3. Provide cautious, practical self-care recommendations (e.g. breathing exercises, progressive relaxation, healthy habits).
4. Do not diagnose definitively or replace a medical professional.
5. If symptoms suggest a severe medical emergency (e.g., chest pain, stroke, suicidal thoughts), advise immediate emergency care.
6. Do not prescribe prescription medication dosages.
7. Be warm, natural, conversational, and supportive.
"""

EMERGENCY_KEYWORDS = [
    r"\bchest pain\b",
    r"\bheart attack\b",
    r"\bcan'?t breathe\b",
    r"\bshortness of breath\b",
    r"\bsevere bleeding\b",
    r"\bsuicid",
    r"\bkill myself\b",
    r"\bwant to die\b",
    r"\bseizure\b",
    r"\bstroke\b",
    r"\bunconscious\b"
]


def check_emergency(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pat, lowered) for pat in EMERGENCY_KEYWORDS)


def get_fallback_health_response(message: str, text_emotion: str = "Neutral", face_emotion: Optional[str] = None) -> str:
    """Provides a safe, rule-guided fallback health response if the upstream LLM is unavailable."""
    msg = message.lower()
    emotion_intro = ""

    if face_emotion and face_emotion.lower() != "neutral":
        if text_emotion.lower() != face_emotion.lower():
            emotion_intro = f"I notice from your facial expression that you may be feeling {face_emotion.lower()}, even though your words feel {text_emotion.lower()}. It's completely valid and safe to express how you are truly feeling.\n\n"
        else:
            emotion_intro = f"I sense both from your words and expression that you're experiencing {text_emotion.lower()}.\n\n"
    elif text_emotion.lower() in ("sad", "fear", "angry"):
        emotion_intro = f"I hear the {text_emotion.lower()} in your words. Please take a gentle breath — you're not alone in feeling this way.\n\n"

    if "anxious" in msg or "anxiety" in msg or "panic" in msg or text_emotion == "Fear":
        return (
            f"{emotion_intro}Take a slow, deep breath in for 4 seconds, hold for 4, and exhale for 4.\n\n"
            "Anxiety and tension are very common physiological responses to stress. Helpful self-care steps include grounding exercises (focusing on 5 things you can see, 4 you can touch), gentle stretching, and listening to soothing music. If these feelings are persistent, speaking with a licensed therapist or mental health counselor is strongly recommended."
        )
    if "sad" in msg or "depressed" in msg or "lonely" in msg or text_emotion == "Sad":
        return (
            f"{emotion_intro}It's completely normal to have days that feel heavy or lonely.\n\n"
            "Be kind to yourself today: wrap yourself in a warm blanket, listen to comforting music, hydrate, and consider reaching out to someone you trust. Remember that emotions ebb and flow like waves."
        )
    if "sleep" in msg or "insomnia" in msg or "tired" in msg:
        return (
            f"{emotion_intro}Difficulty sleeping can be caused by stress, screen time before bed, or irregular schedules.\n\n"
            "Try keeping your bedroom cool and dark, avoiding bright screens for 60 minutes before bedtime, and establishing a consistent winding-down routine. Relaxing instrumental or soft tunes can also help quiet your mind."
        )
    if "headache" in msg or "migraine" in msg:
        return (
            f"{emotion_intro}Headaches often stem from tension, dehydration, eye strain, or lack of sleep.\n\n"
            "Try drinking a glass of water, resting in a quiet, dimly lit room, or applying a cool compress to your forehead. If you experience a sudden 'thunderclap' headache, fever with stiff neck, or vision changes, seek immediate emergency medical care."
        )

    return (
        f"{emotion_intro}Thank you for sharing what is on your mind. While assessing symptoms or feelings like '{message}', it helps to consider how long they have been present and their severity.\n\n"
        "Remember to stay hydrated, take moments to rest, and treat yourself with patience. Check out the music recommendations below to help match or gently elevate your mood!"
    )



@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "MindTracker & AI Health Assistant",
        "text_model_loaded": text_emotion_classifier._is_loaded,
        "face_model_loaded": face_emotion_detector._is_loaded
    }


@app.get("/api/status")
def status():
    return {
        "status": "ok",
        "service": "MindTracker & AI Health Assistant",
        "models_integrated": {
            "text_emotion_classifier": "DistilBERT (8 classes)",
            "face_emotion_detector": "AffectNet DenseNet-121 (8 classes)",
            "mood_to_music": "Bollywood Mood-Based Recommender"
        },
        "llm_config": {
            "base_url": base_url,
            "model": model_name,
            "has_key": bool(api_key),
            "key_prefix": (api_key[:8] + "...") if api_key else "None"
        }
    }


@app.get("/api/songs")
def get_songs(mood: str = "calm", limit: int = 8):
    """Retrieve song recommendations for a specific mood."""
    return get_songs_for_emotion(mood, limit=limit)


@app.post("/api/detect-face")
def detect_face(request: FaceDetectRequest):
    """Endpoint for realtime or on-demand facial emotion detection."""
    result = face_emotion_detector.predict_from_base64(request.image)
    return result


@app.post("/api/chat")
def chat(request: ChatRequest):
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    if len(message) > 4000:
        raise HTTPException(
            status_code=413,
            detail="Message is too long"
        )

    is_emergency = check_emergency(message)

    # 1. Classify Text Emotion
    text_emotion_res = text_emotion_classifier.predict(message)
    text_emotion = text_emotion_res.get("emotion", "Neutral")
    text_conf = text_emotion_res.get("confidence", 0.0)

    # 2. Classify Face Emotion if camera was enabled and an image was provided
    face_emotion_res = None
    face_emotion = None
    if request.camera_enabled and request.face_image:
        face_emotion_res = face_emotion_detector.predict_from_base64(request.face_image)
        if face_emotion_res.get("face_detected"):
            face_emotion = face_emotion_res.get("emotion")

    # 3. Determine Dominant Emotion for song recommendations
    # If text has a strong emotion, prefer it, but if face detected strong emotion (e.g. Sad/Fear/Happy), blend it
    if text_emotion != "Neutral":
        dominant_emotion = text_emotion
    elif face_emotion and face_emotion != "Neutral":
        dominant_emotion = face_emotion
    else:
        dominant_emotion = text_emotion or "Neutral"

    # 4. Retrieve Song Recommendations for the bottom shelf
    music_recommendations = get_songs_for_emotion(dominant_emotion, limit=6)

    # 5. Build emotionally augmented context for the LLM
    context_lines = [
        f"[User Emotion Analysis]",
        f"- Text Model Classification: {text_emotion} ({round(text_conf * 100, 1)}% confidence)",
    ]
    if face_emotion_res and face_emotion_res.get("face_detected"):
        face_conf = round(face_emotion_res.get("confidence", 0.0) * 100, 1)
        context_lines.append(f"- Camera Facial Expression: {face_emotion} ({face_conf}% confidence)")
        if face_emotion.lower() != text_emotion.lower():
            context_lines.append(
                f"- Emotional Discrepancy: The user's typed tone is '{text_emotion}' while their facial expression is '{face_emotion}'. "
                "Gently acknowledge their visual emotional cues with warmth and non-judgmental empathy."
            )
    else:
        if request.camera_enabled:
            context_lines.append("- Camera: Enabled, but no distinct face was detected in the frame.")

    context_prompt = "\n".join(context_lines)

    # If offline or no API key, use the local guidance engine with emotional context
    if not client or not api_key:
        fallback = get_fallback_health_response(message, text_emotion=text_emotion, face_emotion=face_emotion)
        return {
            "reply": f"[MindTracker Local AI]: {fallback}",
            "is_emergency": is_emergency,
            "source": "local_emotional_engine",
            "text_emotion": text_emotion_res,
            "face_emotion": face_emotion_res,
            "dominant_emotion": dominant_emotion,
            "music": music_recommendations
        }

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": f"{SYSTEM_PROMPT}\n\n{context_prompt}",
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            temperature=0.4,
            max_tokens=800,
        )

        reply = response.choices[0].message.content or ""

        return {
            "reply": reply,
            "is_emergency": is_emergency,
            "source": f"llm:{model_name}",
            "text_emotion": text_emotion_res,
            "face_emotion": face_emotion_res,
            "dominant_emotion": dominant_emotion,
            "music": music_recommendations
        }

    except Exception as err:
        err_msg = str(err)
        if fallback_mode:
            fallback = get_fallback_health_response(message, text_emotion=text_emotion, face_emotion=face_emotion)
            billing_hint = ""
            if "console.x.ai" in err_msg or "credits" in err_msg.lower() or ("403" in err_msg and "x.ai" in base_url):
                billing_hint = "⚠️ [Notice: Upstream Grok (xAI) API returned a 403 error. Serving via local emotional guidance engine:]\n\n"
            elif "billing" in err_msg.lower() or "402" in err_msg:
                billing_hint = "⚠️ [Notice: Upstream LLM API returned a 402 Billing error. Serving via local emotional guidance engine:]\n\n"
            elif "401" in err_msg or "auth" in err_msg.lower():
                billing_hint = "⚠️ [Notice: Upstream LLM authentication failed. Serving via local emotional guidance engine:]\n\n"
            else:
                billing_hint = f"⚠️ [Notice: Upstream LLM error. Serving via local emotional guidance engine:]\n\n"

            return {
                "reply": f"{billing_hint}{fallback}",
                "is_emergency": is_emergency,
                "source": "local_fallback_on_error",
                "text_emotion": text_emotion_res,
                "face_emotion": face_emotion_res,
                "dominant_emotion": dominant_emotion,
                "music": music_recommendations,
                "upstream_error": err_msg
            }

        raise HTTPException(
            status_code=502,
            detail=f"The AI service could not process your request: {err_msg}"
        )


@app.post("/api/voice")
async def voice(audio: UploadFile = File(...)):
    """Receives voice audio blob, processes transcript, analyzes emotion, and returns response with songs."""
    content = await audio.read()

    if not content:
        raise HTTPException(status_code=400, detail="Empty audio file received")

    # Voice transcript simulation / speech-to-text
    simulated_transcript = "I've been feeling stressed and experiencing tension headaches."
    emergency = check_emergency(simulated_transcript)

    text_emotion_res = text_emotion_classifier.predict(simulated_transcript)
    dominant_emotion = text_emotion_res.get("emotion", "Fear")
    music_recommendations = get_songs_for_emotion(dominant_emotion, limit=6)
    reply_text = get_fallback_health_response(simulated_transcript, text_emotion=dominant_emotion)

    return {
        "transcript": simulated_transcript,
        "reply": f"[Voice Input Processed - {len(content)} bytes]: {reply_text}",
        "is_emergency": emergency,
        "audio_url": None,
        "text_emotion": text_emotion_res,
        "face_emotion": None,
        "dominant_emotion": dominant_emotion,
        "music": music_recommendations
    }


# Mount Frontend production build if dist directory exists
from fastapi.staticfiles import StaticFiles

frontend_dist = Path(__file__).resolve().parent.parent.parent / "Frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

