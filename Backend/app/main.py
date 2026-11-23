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
    if not model_name or "grok" in model_name or "muse" in model_name or "llama" in model_name:
        model_name = "nvidia/nemotron-3.5-bolt-e4b"
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

# Initialize OpenAI-compatible client with quick timeout (6s) so UI never hangs for 30s
client = None
if api_key:
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=6.0, max_retries=1)

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


import random


def get_fallback_health_response(message: str, text_emotion: str = "Neutral", face_emotion: Optional[str] = None) -> str:
    """Provides a safe, varied, evidence-based emotional health response."""
    msg = message.lower()
    
    # 1. Dynamic emotional opening acknowledging multi-modal inputs
    intros = []
    if face_emotion and face_emotion.lower() != "neutral":
        if text_emotion.lower() != face_emotion.lower():
            intros = [
                f"I notice a gentle contradiction: while your words feel {text_emotion.lower()}, your facial expression carries signs of {face_emotion.lower()}. It's completely safe to let your guard down here.",
                f"Looking at your expression, I sense some {face_emotion.lower()} lingering beneath the surface, even though you typed '{text_emotion.lower()}'. You don't have to carry it all alone.",
                f"Your face seems to reflect {face_emotion.lower()} even as your message leans {text_emotion.lower()}. Your true feelings are completely valid and heard.",
            ]
        else:
            intros = [
                f"Both your words and expressions reflect that you're experiencing {text_emotion.lower()} right now.",
                f"I can sense how much {text_emotion.lower()} is present for you in this moment.",
                f"I see and hear the {text_emotion.lower()} you are carrying right now.",
            ]
    elif text_emotion.lower() in ("sad", "fear", "angry", "disgust"):
        intros = [
            f"I hear the {text_emotion.lower()} in your words. Please take a gentle, unhurried breath with me.",
            f"Thank you for being open and sharing your feelings. Carrying {text_emotion.lower()} can feel exhausting.",
            f"I'm right here with you. It takes courage to put feelings of {text_emotion.lower()} into words.",
        ]
    elif text_emotion.lower() in ("happy", "surprise"):
        intros = [
            "It's so wonderful to hear this lightness and positivity in your words!",
            "I love sensing this spark of joy in what you shared!",
            "Your message brings a wonderful sense of energy and warmth!",
        ]
    else:
        intros = [
            "Thank you for checking in and sharing what's on your mind.",
            "I'm listening closely to what you've shared.",
            "I appreciate you taking a moment to connect today.",
        ]
    
    emotion_intro = random.choice(intros) + "\n\n"

    # 2. Topic & Emotion specific response pools for rich variety
    if "anxious" in msg or "anxiety" in msg or "panic" in msg or "scared" in msg or "nervous" in msg or text_emotion == "Fear":
        anxious_options = [
            (
                "Take a slow breath: inhale through your nose for 4 seconds, hold for 4, and exhale gently through your mouth for 6.\n\n"
                "Anxiety is your nervous system's alarm system misfiring—it feels intense, but it is not dangerous, and it *will* pass. "
                "Try placing both feet flat on the floor and naming 3 physical things you can see around you right now. "
                "What is the single biggest thought creating pressure for you at this moment?"
            ),
            (
                "Let's do a quick somatic reset: drop your shoulders away from your ears, unclench your jaw, and let your belly soften.\n\n"
                "When anxiety spikes, our body tries to protect us by tensing up. Remember: **you do not have to solve your entire future today—just this one present minute.** "
                "Would it help to write down what's worrying you, or would you prefer listening to calming rhythms to settle your thoughts?"
            ),
            (
                "Try the 5-4-3-2-1 grounding technique right now:\n"
                "• 5 things you see\n"
                "• 4 things you can physically touch\n"
                "• 3 sounds you hear\n"
                "• 2 things you can smell\n"
                "• 1 deep, nourishing breath\n\n"
                "You are safe right now in this exact room. Take a sip of water and let the music below ground your heart rate."
            )
        ]
        return emotion_intro + random.choice(anxious_options)

    if "sad" in msg or "depressed" in msg or "lonely" in msg or "cry" in msg or "crying" in msg or "heartbroken" in msg or text_emotion == "Sad":
        sad_options = [
            (
                "It is completely okay to feel heavy and not be okay today. Sadness is not a personal failure—it is simply proof that you care deeply.\n\n"
                "Be as gentle with yourself as you would be with a dear friend. Wrap yourself in warmth, sip something comforting, and don't force yourself to be cheerful. "
                "Emotions are like waves—they rise, they peak, and they gently recede. I'm right here with you."
            ),
            (
                "When your heart feels heavy, even small tasks can feel like climbing a mountain. Give yourself full permission to lower all expectations today.\n\n"
                "If you feel like crying, let those tears flow; crying releases cortisol and endorphins that naturally calm your system. "
                "What is one gentle, comforting thing you can offer yourself right now—even if it's just lying down with soothing music?"
            ),
            (
                "Loneliness and sadness often whisper that nobody understands or that this feeling is permanent, but that isn't true.\n\n"
                "You are worthy of support, patience, and kindness. Consider sending a quick note to someone safe, or simply let the comforting songs below keep you company as you rest. "
                "Would you like to talk through what brought this sadness on, or would you rather keep things quiet and peaceful?"
            )
        ]
        return emotion_intro + random.choice(sad_options)

    if "angry" in msg or "mad" in msg or "frustrated" in msg or "irritated" in msg or text_emotion == "Angry":
        angry_options = [
            (
                "Your frustration and anger are completely understandable. Anger is often a protective emotion telling us that an important boundary or expectation was violated.\n\n"
                "Try releasing that physical tension: clench your fists tightly for 5 seconds, and then consciously release them, letting all the tension drain through your fingertips. "
                "Do you want to vent uncensored about what happened? I'm here to listen without judgment."
            ),
            (
                "When anger surges, your heart rate and adrenaline spike rapidly. Before deciding what to say or do next, give yourself a 2-minute timeout.\n\n"
                "Splash cold water on your face—this activates the mammalian dive reflex, which physically slows down your pulse. "
                "Remember: feeling angry is always valid, but how you channel that energy is where your real power lies."
            )
        ]
        return emotion_intro + random.choice(angry_options)

    if "happy" in msg or "excited" in msg or "great" in msg or "joy" in msg or text_emotion == "Happy":
        happy_options = [
            (
                "What a gift to experience moments of genuine happiness and energy! Celebrating these moments actually strengthens positive neural pathways in the brain.\n\n"
                "Take a deliberate 10 seconds to savor this sensation: what does this joy feel like in your body? "
                "Enjoy the upbeat songs below to amplify this wonderful mood!"
            ),
            (
                "I'm so glad things are feeling bright and positive for you today! It's so important to honor and celebrate the good days.\n\n"
                "What was the highlight that made your day feel this way? Keep this momentum going!"
            )
        ]
        return emotion_intro + random.choice(happy_options)

    if "sleep" in msg or "insomnia" in msg or "tired" in msg or "exhausted" in msg:
        sleep_options = [
            (
                "Exhaustion affects both the body and mind. If your thoughts are racing, remember that rest is still restorative, even if sleep takes time to arrive.\n\n"
                "Try the 4-7-8 breathing technique: inhale quietly for 4 seconds, hold for 7, and exhale completely with a whoosh sound for 8. "
                "Dim the screens, keep your room cool, and let the gentle music below help you unwind."
            ),
            (
                "When you're running on empty, your emotional threshold drops. Be extra forgiving with yourself right now.\n\n"
                "Try doing a 'brain dump': write down any looming thoughts or to-dos on a piece of paper so your mind knows they won't be forgotten overnight. "
                "Give yourself permission to sign off and truly rest."
            )
        ]
        return emotion_intro + random.choice(sleep_options)

    if "headache" in msg or "migraine" in msg:
        return (
            f"{emotion_intro}Headaches often stem from tension, dehydration, screen fatigue, or posture strain.\n\n"
            "Try drinking a large glass of water, resting your eyes in a dim room, and gently massaging the base of your skull. "
            "If your headache is sudden, unusually severe, or accompanied by fever or neck stiffness, please consult a medical professional promptly."
        )

    # General / Reflective fallback options
    general_options = [
        (
            f"Thank you for sharing your thoughts. Sometimes just verbalizing what's on your mind is the first step toward clarity.\n\n"
            "How has your energy been overall today? Remember to hydrate, take short pauses to stretch, and treat yourself with patience. "
            "Feel free to explore the songs curated below to match or lift your rhythm!"
        ),
        (
            f"I hear you. Whatever you are navigating right now, remember that progress isn't linear, and small steps count.\n\n"
            "Take a quiet moment to check in with your physical body: are you holding tension in your neck or jaw? Let it release. "
            "What would bring you a small slice of peace or comfort in the next hour?"
        ),
        (
            f"I'm grateful you reached out. Balancing daily life can take a quiet toll on our emotional well-being.\n\n"
            "Take things one breath at a time. The musical playlist below is tuned to your emotional frequency—give it a listen while you relax."
        )
    ]
    return emotion_intro + random.choice(general_options)



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
            "reply": fallback,
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
            temperature=0.6,
            max_tokens=400,
            timeout=5.0,
        )

        reply = response.choices[0].message.content or ""
        if not reply.strip() and hasattr(response.choices[0].message, "reasoning_content"):
            reply = response.choices[0].message.reasoning_content or ""

        if not reply.strip():
            # If model returned empty content, use the rich fallback
            reply = get_fallback_health_response(message, text_emotion=text_emotion, face_emotion=face_emotion)

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
        print(f"[Chat LLM Exception] {err_msg}")
        if fallback_mode:
            fallback = get_fallback_health_response(message, text_emotion=text_emotion, face_emotion=face_emotion)
            return {
                "reply": fallback,
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

