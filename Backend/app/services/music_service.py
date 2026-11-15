import random
import urllib.parse
from typing import List, Dict, Any

# Bollywood Song Database categorized by emotional tone
SONG_DB = {
    "happy": [
        {"title": "Badtameez Dil", "artist": "Pritam, Benny Dayal", "movie": "Yeh Jawaani Hai Deewani", "genre": "Pop/Dance", "bpm": "128 BPM", "icon": "🎉"},
        {"title": "London Thumakda", "artist": "Labh Janjua, Sonu Kakkar", "movie": "Queen", "genre": "Folk/Dance", "bpm": "130 BPM", "icon": "💃"},
        {"title": "Gallan Goodiyaan", "artist": "Shilpa Rao, Yashita Sharma", "movie": "Dil Dhadakne Do", "genre": "Pop/Dance", "bpm": "120 BPM", "icon": "🥳"},
        {"title": "Kar Gayi Chull", "artist": "Badshah, Neha Kakkar", "movie": "Kapoor & Sons", "genre": "Dance/Pop", "bpm": "126 BPM", "icon": "🕺"},
        {"title": "Balam Pichkari", "artist": "Vishal Dadlani, Shalmali", "movie": "Yeh Jawaani Hai Deewani", "genre": "Folk/Pop", "bpm": "119 BPM", "icon": "🌈"},
        {"title": "Nagada Sang Dhol", "artist": "Shreya Ghoshal, Osman Mir", "movie": "Ram-Leela", "genre": "Folk/Dance", "bpm": "132 BPM", "icon": "🥁"},
        {"title": "Tune Maari Entriyaan", "artist": "Vishal Dadlani, KK", "movie": "Gunday", "genre": "Pop", "bpm": "118 BPM", "icon": "😄"},
        {"title": "Dhoom Machale", "artist": "Sunidhi Chauhan", "movie": "Dhoom", "genre": "Dance", "bpm": "135 BPM", "icon": "☀️"},
    ],
    "sad": [
        {"title": "Channa Mereya", "artist": "Arijit Singh", "movie": "Ae Dil Hai Mushkil", "genre": "Acoustic", "bpm": "74 BPM", "icon": "💔"},
        {"title": "Tum Hi Ho", "artist": "Arijit Singh", "movie": "Aashiqui 2", "genre": "Ballad", "bpm": "68 BPM", "icon": "🌧️"},
        {"title": "Kabhi Jo Baadal Barse", "artist": "Arijit Singh", "movie": "Jackpot", "genre": "Acoustic", "bpm": "65 BPM", "icon": "🌧️"},
        {"title": "Galliyan", "artist": "Ankit Tiwari", "movie": "Ek Villain", "genre": "Ballad", "bpm": "72 BPM", "icon": "🖤"},
        {"title": "Phir Le Aaya Dil", "artist": "Arijit Singh", "movie": "Barfi!", "genre": "Lo-fi", "bpm": "63 BPM", "icon": "😢"},
        {"title": "Ae Dil Hai Mushkil", "artist": "Arijit Singh", "movie": "Ae Dil Hai Mushkil", "genre": "Ballad", "bpm": "70 BPM", "icon": "💧"},
        {"title": "Jeena Jeena", "artist": "Atif Aslam", "movie": "Badlapur", "genre": "Acoustic", "bpm": "75 BPM", "icon": "🍂"},
        {"title": "Tera Yaar Hoon Main", "artist": "Arijit Singh", "movie": "Sonu Ke Titu Ki Sweety", "genre": "Soft Rock", "bpm": "78 BPM", "icon": "🕊️"},
    ],
    "calm": [
        {"title": "Kun Faya Kun", "artist": "AR Rahman, Javed Ali", "movie": "Rockstar", "genre": "Sufi", "bpm": "58 BPM", "icon": "🕌"},
        {"title": "Aaoge Jab Tum", "artist": "Ustad Rashid Khan", "movie": "Jab We Met", "genre": "Classical", "bpm": "55 BPM", "icon": "🌸"},
        {"title": "Tere Bina", "artist": "AR Rahman, Chinmayi", "movie": "Guru", "genre": "Sufi/Chill", "bpm": "72 BPM", "icon": "🌅"},
        {"title": "Roke Na Ruke Naina", "artist": "Arijit Singh", "movie": "Wazir", "genre": "Soft Pop", "bpm": "68 BPM", "icon": "🌙"},
        {"title": "Noor E Khuda", "artist": "Adnan Sami, Shreya Ghoshal", "movie": "My Name Is Khan", "genre": "Devotional", "bpm": "62 BPM", "icon": "✨"},
        {"title": "Tujhe Bhula Diya", "artist": "Mohit Chauhan", "movie": "Anjaana Anjaani", "genre": "Soft", "bpm": "75 BPM", "icon": "☁️"},
        {"title": "Ik Vaari Aa", "artist": "Arijit Singh", "movie": "Raabta", "genre": "Chill", "bpm": "80 BPM", "icon": "🌿"},
        {"title": "O Re Piya", "artist": "Rahat Fateh Ali Khan", "movie": "Aaja Nachle", "genre": "Sufi", "bpm": "58 BPM", "icon": "🌊"},
    ],
    "stressed": [
        {"title": "Kal Ho Na Ho", "artist": "Sonu Nigam", "movie": "Kal Ho Na Ho", "genre": "Soft", "bpm": "60 BPM", "icon": "🌤️"},
        {"title": "Dil Se Re", "artist": "AR Rahman", "movie": "Dil Se", "genre": "Instrumental", "bpm": "52 BPM", "icon": "💆"},
        {"title": "Yeh Jo Des Hai Tera", "artist": "AR Rahman", "movie": "Swades", "genre": "Instrumental", "bpm": "50 BPM", "icon": "🌿"},
        {"title": "Alvida", "artist": "KK", "movie": "Life in a Metro", "genre": "Soft Rock", "bpm": "70 BPM", "icon": "🍃"},
        {"title": "Teri Meri", "artist": "Rahat Fateh Ali Khan", "movie": "Bodyguard", "genre": "Sufi Soft", "bpm": "60 BPM", "icon": "🌾"},
        {"title": "Jab Tak Hai Jaan", "artist": "AR Rahman", "movie": "Jab Tak Hai Jaan", "genre": "Soft", "bpm": "65 BPM", "icon": "🕯️"},
        {"title": "Mann Ko Dheer De", "artist": "Shreya Ghoshal", "movie": "Kal Ho Na Ho", "genre": "Soothing", "bpm": "55 BPM", "icon": "🧘"},
        {"title": "Sooraj Ki Baahon Mein", "artist": "Shreya Ghoshal, Mohit", "movie": "Ek Main Aur Ekk Tu", "genre": "Soft Pop", "bpm": "63 BPM", "icon": "☀️"},
    ],
    "excited": [
        {"title": "Malhari", "artist": "Vishal Dadlani", "movie": "Bajirao Mastani", "genre": "EDM/Folk", "bpm": "135 BPM", "icon": "⚡"},
        {"title": "Zinda", "artist": "Siddharth Mahadevan", "movie": "Bhaag Milkha Bhaag", "genre": "Rock", "bpm": "130 BPM", "icon": "🔥"},
        {"title": "Tattad Tattad", "artist": "Aditya Narayan", "movie": "Ram-Leela", "genre": "EDM", "bpm": "128 BPM", "icon": "💥"},
        {"title": "Swag Se Swagat", "artist": "Vishal-Shekhar", "movie": "Tiger Zinda Hai", "genre": "Dance/EDM", "bpm": "125 BPM", "icon": "🦁"},
        {"title": "Dhan Te Nan", "artist": "Sukhwinder Singh", "movie": "Kaminey", "genre": "Rock/Fusion", "bpm": "132 BPM", "icon": "🎸"},
        {"title": "Sadda Haq", "artist": "Mohit Chauhan", "movie": "Rockstar", "genre": "Rock", "bpm": "120 BPM", "icon": "🤘"},
        {"title": "Jumme Ki Raat", "artist": "Mika Singh", "movie": "Kick", "genre": "Dance", "bpm": "126 BPM", "icon": "🕺"},
        {"title": "Bhaag DK Bose", "artist": "Ram Sampath", "movie": "Delhi Belly", "genre": "Rock/Punk", "bpm": "140 BPM", "icon": "💨"},
    ],
    "angry": [
        {"title": "Dhaakad", "artist": "Pritam", "movie": "Dangal", "genre": "Power", "bpm": "112 BPM", "icon": "💪"},
        {"title": "Sultan Theme", "artist": "Vishal-Shekhar", "movie": "Sultan", "genre": "Power/Rock", "bpm": "108 BPM", "icon": "👊"},
        {"title": "War Anthem", "artist": "Vishal-Shekhar", "movie": "War", "genre": "Action", "bpm": "122 BPM", "icon": "⚡"},
        {"title": "Ghungroo", "artist": "Arijit Singh, Shilpa Rao", "movie": "War", "genre": "Intense", "bpm": "120 BPM", "icon": "💢"},
        {"title": "Singham Returns", "artist": "Sukhwinder Singh", "movie": "Singham Returns", "genre": "Power", "bpm": "116 BPM", "icon": "😠"},
        {"title": "Ziddi Dil", "artist": "Vishal Dadlani", "movie": "Mary Kom", "genre": "Rock", "bpm": "118 BPM", "icon": "🔥"},
        {"title": "Toofan", "artist": "Shankar Mahadevan", "movie": "Toofan", "genre": "Power", "bpm": "114 BPM", "icon": "🌪️"},
        {"title": "Ek Do Teen (Remix)", "artist": "Alka Yagnik", "movie": "Baaghi 2", "genre": "High Energy", "bpm": "118 BPM", "icon": "😤"},
    ],
    "neutral": [
        {"title": "Zoobi Doobi", "artist": "Shaan, Shreya Ghoshal", "movie": "3 Idiots", "genre": "Light Pop", "bpm": "112 BPM", "icon": "🎵"},
        {"title": "Jai Ho", "artist": "AR Rahman", "movie": "Slumdog Millionaire", "genre": "World", "bpm": "120 BPM", "icon": "🌍"},
        {"title": "Bulleya", "artist": "Amit Mishra", "movie": "Sultan", "genre": "Sufi Pop", "bpm": "95 BPM", "icon": "🌤️"},
        {"title": "Ude Dil Befikre", "artist": "Vishal-Shekhar", "movie": "Befikre", "genre": "Pop", "bpm": "102 BPM", "icon": "🕊️"},
        {"title": "Aankh Marey", "artist": "Mika Singh, Neha Kakkar", "movie": "Simmba", "genre": "Retro Pop", "bpm": "110 BPM", "icon": "😎"},
        {"title": "Dilbaro", "artist": "Shankar-Ehsaan-Loy", "movie": "Raazi", "genre": "Folk Soft", "bpm": "80 BPM", "icon": "🌾"},
        {"title": "Baar Baar Dekho", "artist": "Bilal Saeed", "movie": "Baar Baar Dekho", "genre": "Pop", "bpm": "108 BPM", "icon": "👀"},
        {"title": "Khwaja Mere Khwaja", "artist": "AR Rahman", "movie": "Jodhaa Akbar", "genre": "Sufi", "bpm": "85 BPM", "icon": "🎶"},
    ],
}

EMOTION_META = {
    "happy": {"icon": "😊", "name": "Joy & Happiness", "desc": "Energetic Bollywood beats to celebrate your positive mood!", "genre": "Pop / Dance", "color": "#f59e0b"},
    "sad": {"icon": "😢", "name": "Comfort & Solace", "desc": "Heartfelt, soulful melodies to bring comfort to your heart", "genre": "Acoustic / Ballad", "color": "#3b82f6"},
    "calm": {"icon": "😌", "name": "Peace & Calm", "desc": "Sufi and gentle tunes to center your mind and relax", "genre": "Sufi / Chill", "color": "#10b981"},
    "stressed": {"icon": "💆", "name": "Stress Relief", "desc": "Deeply soothing melodies to reduce tension and anxiety", "genre": "Instrumental / Soft", "color": "#8b5cf6"},
    "excited": {"icon": "⚡", "name": "Energy & Excitement", "desc": "High-octane tracks to match your thrilling energy!", "genre": "EDM / Rock", "color": "#f97316"},
    "angry": {"icon": "🔥", "name": "Power & Release", "desc": "High intensity tracks to channel and release strong emotions", "genre": "Power / Action", "color": "#ef4444"},
    "neutral": {"icon": "🎧", "name": "Balanced & Easy", "desc": "Pleasant, mellow melodies for steady focus and peace of mind", "genre": "Mixed / Pop", "color": "#6b7280"},
}

# Emotion classification to song mood mapping
MOOD_MAPPING = {
    "Happy": "happy",
    "Smiling": "happy",
    "Sad": "sad",
    "Fear": "stressed",
    "Angry": "angry",
    "Disgust": "angry",
    "Contempt": "angry",
    "Surprise": "excited",
    "Neutral": "calm",
}


def map_emotion_to_music_mood(emotion: str) -> str:
    """Normalizes raw model prediction to one of our song mood categories."""
    if not emotion:
        return "neutral"
    normalized = emotion.strip().capitalize()
    return MOOD_MAPPING.get(normalized, "calm")


def get_songs_for_emotion(emotion: str, limit: int = 6) -> Dict[str, Any]:
    """Retrieves formatted song recommendations for a detected emotion."""
    mood = map_emotion_to_music_mood(emotion)
    song_list = SONG_DB.get(mood, SONG_DB["neutral"])

    # Shuffle for fresh recommendations each time
    selected = random.sample(song_list, min(limit, len(song_list)))

    formatted_songs = []
    for s in selected:
        query = f"{s['title']} {s['artist']} bollywood"
        encoded_query = urllib.parse.quote_plus(query)
        yt_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        formatted_songs.append({
            **s,
            "youtube_url": yt_url
        })

    meta = EMOTION_META.get(mood, EMOTION_META["neutral"])

    return {
        "mood_category": mood,
        "emotion_name": meta["name"],
        "icon": meta["icon"],
        "description": meta["desc"],
        "genre": meta["genre"],
        "color": meta["color"],
        "songs": formatted_songs,
        "total_available": len(song_list)
    }
