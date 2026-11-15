import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

# Ensure Anaconda DLLs are available for PIL/Torch on Windows
if sys.platform == "win32" and os.path.exists(r"D:\Anaconda\Library\bin"):
    try:
        os.add_dll_directory(r"D:\Anaconda\Library\bin")
    except Exception:
        pass

# Model labels for DistilBERT emotion classifier
ID2LABEL = {
    0: "Angry",
    1: "Contempt",
    2: "Disgust",
    3: "Fear",
    4: "Happy",
    5: "Neutral",
    6: "Sad",
    7: "Surprise",
}

# Rule-based fallback keywords for graceful degradation
KEYWORD_MOODS = {
    "Sad": ["sad", "depressed", "cry", "crying", "unhappy", "heartbroken", "lonely", "alone", "hopeless", "grief", "miserable", "down", "udaas", "dukh"],
    "Fear": ["fear", "anxious", "anxiety", "scared", "terrified", "panic", "worried", "worry", "nervous", "stressed", "stress", "tension", "darr"],
    "Angry": ["angry", "mad", "furious", "rage", "irritated", "annoyed", "hate", "frustrated", "gussa", "naraaz"],
    "Happy": ["happy", "joy", "joyful", "great", "wonderful", "amazing", "good", "cheerful", "glad", "blessed", "khush", "mazaa"],
    "Surprise": ["surprised", "shocked", "amazed", "astonished", "wow", "unbelievable"],
    "Disgust": ["disgusted", "gross", "revolting", "nauseating", "sick", "awful"],
    "Contempt": ["worthless", "pathetic", "disdain", "scorn"],
}


class TextEmotionClassifier:
    def __init__(self, model_dir: Path = None):
        if model_dir is None:
            model_dir = Path(__file__).resolve().parent.parent.parent / "model_weights" / "text_emotion_model"
        self.model_dir = model_dir
        self.tokenizer = None
        self.model = None
        self.device = "cpu"
        self._is_loaded = False

    def load(self):
        if self._is_loaded:
            return

        import torch
        from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[TextEmotionClassifier] Loading model from {self.model_dir} on {self.device}...")

        if not self.model_dir.exists():
            print(f"[TextEmotionClassifier] Warning: Model dir {self.model_dir} does not exist.")
            return

        self.tokenizer = DistilBertTokenizer.from_pretrained(str(self.model_dir))
        self.model = DistilBertForSequenceClassification.from_pretrained(str(self.model_dir))
        self.model.to(self.device)
        self.model.eval()
        self._is_loaded = True
        print("[TextEmotionClassifier] Model loaded successfully.")

    def fallback_predict(self, text: str) -> Dict[str, Any]:
        """Simple rule-based fallback if model is unavailable."""
        lowered = text.lower()
        counts = {emotion: sum(1 for kw in kws if kw in lowered) for emotion, kws in KEYWORD_MOODS.items()}
        top_emotion, top_count = max(counts.items(), key=lambda x: x[1])
        if top_count > 0:
            return {
                "emotion": top_emotion,
                "confidence": 0.75,
                "probabilities": {k: (0.75 if k == top_emotion else 0.04) for k in ID2LABEL.values()},
                "source": "keyword_fallback"
            }
        return {
            "emotion": "Neutral",
            "confidence": 0.60,
            "probabilities": {k: (0.60 if k == "Neutral" else 0.05) for k in ID2LABEL.values()},
            "source": "keyword_fallback"
        }

    def predict(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "emotion": "Neutral",
                "confidence": 1.0,
                "probabilities": {k: (1.0 if k == "Neutral" else 0.0) for k in ID2LABEL.values()},
                "source": "default"
            }

        if not self._is_loaded:
            try:
                self.load()
            except Exception as e:
                print(f"[TextEmotionClassifier] Failed to load model dynamically: {e}")
                return self.fallback_predict(text)

        if not self._is_loaded or self.model is None or self.tokenizer is None:
            return self.fallback_predict(text)

        import torch

        try:
            encoding = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=256
            )
            input_ids = encoding["input_ids"].to(self.device)
            attention_mask = encoding["attention_mask"].to(self.device)

            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                probs = torch.softmax(outputs.logits, dim=1)
                pred_class = torch.argmax(probs, dim=1).item()
                confidence = probs[0][pred_class].item()
                all_probs = probs[0].cpu().numpy().tolist()

            emotion = ID2LABEL.get(pred_class, "Neutral")
            prob_dict = {ID2LABEL[i]: round(all_probs[i], 4) for i in range(len(ID2LABEL))}

            return {
                "emotion": emotion,
                "confidence": round(confidence, 4),
                "probabilities": prob_dict,
                "source": "distilbert"
            }
        except Exception as e:
            print(f"[TextEmotionClassifier] Inference error: {e}")
            return self.fallback_predict(text)


# Global singleton instance
text_emotion_classifier = TextEmotionClassifier()
