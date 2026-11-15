import os
import sys
import base64
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure Anaconda DLLs are available for PIL/Torch on Windows
if sys.platform == "win32" and os.path.exists(r"D:\Anaconda\Library\bin"):
    try:
        os.add_dll_directory(r"D:\Anaconda\Library\bin")
    except Exception:
        pass

# Label mapping for AffectNet DenseNet-121 classifier
EMOTION_MAP = {
    0: "Neutral",
    1: "Disgust",
    2: "Surprise",
    3: "Happy",
    4: "Sad",
    5: "Angry",
    6: "Fear",
    7: "Smiling"
}


class FaceEmotionDetector:
    def __init__(self, model_path: Path = None, cascade_path: Path = None):
        weights_dir = Path(__file__).resolve().parent.parent.parent / "model_weights" / "face_model"
        if model_path is None:
            model_path = weights_dir / "best_affectnet_model_V3.pth"
        if cascade_path is None:
            cascade_path = weights_dir / "haarcascade_frontalface_default.xml"

        self.model_path = model_path
        self.cascade_path = cascade_path
        self.model = None
        self.face_cascade = None
        self.transform = None
        self.device = "cpu"
        self._is_loaded = False

    def load(self):
        if self._is_loaded:
            return

        from PIL import Image
        import torch
        import torch.nn as nn
        import cv2
        from torchvision.models import densenet121
        from torchvision import transforms

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[FaceEmotionDetector] Loading DenseNet model from {self.model_path} on {self.device}...")

        if not self.model_path.exists():
            print(f"[FaceEmotionDetector] Warning: Model file {self.model_path} not found.")
            return

        model = densenet121(weights=None)
        model.classifier = nn.Linear(model.classifier.in_features, 8)
        state = torch.load(str(self.model_path), map_location=self.device)
        model.load_state_dict(state)
        model.to(self.device)
        model.eval()
        self.model = model

        # Load OpenCV face cascade (gracefully skip if CascadeClassifier unavailable)
        try:
            if hasattr(cv2, 'CascadeClassifier'):
                if self.cascade_path.exists():
                    self.face_cascade = cv2.CascadeClassifier(str(self.cascade_path))
                elif hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
                    default_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
                    self.face_cascade = cv2.CascadeClassifier(default_path)
            else:
                print("[FaceEmotionDetector] cv2.CascadeClassifier not available — using center-crop fallback.")
                self.face_cascade = None
        except Exception as e:
            print(f"[FaceEmotionDetector] Cascade load warning: {e} — using center-crop fallback.")
            self.face_cascade = None

        # Standard ImageNet / AffectNet image preprocessing
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                [0.485, 0.456, 0.406],
                [0.229, 0.224, 0.225]
            )
        ])

        self._is_loaded = True
        print("[FaceEmotionDetector] Model and face cascade loaded successfully.")

    def predict_from_base64(self, image_data: str) -> Dict[str, Any]:
        """Accepts base64 encoded image string (with or without data URL prefix)."""
        if not image_data:
            return {"face_detected": False, "emotion": "Unknown", "confidence": 0.0, "error": "No image provided"}

        if not self._is_loaded:
            try:
                self.load()
            except Exception as e:
                print(f"[FaceEmotionDetector] Failed to load model: {e}")
                return {"face_detected": False, "emotion": "Unknown", "confidence": 0.0, "error": str(e)}

        if not self._is_loaded or self.model is None:
            return {"face_detected": False, "emotion": "Unknown", "confidence": 0.0, "error": "Model not loaded"}

        import numpy as np
        import cv2
        import torch

        try:
            # Strip data URL header if present (e.g. data:image/jpeg;base64,...)
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]

            image_bytes = base64.b64decode(image_data)
            np_arr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None or frame.size == 0:
                return {"face_detected": False, "emotion": "Unknown", "confidence": 0.0, "error": "Invalid image format"}

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = ()
            if self.face_cascade and not self.face_cascade.empty():
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=4,
                    minSize=(40, 40)
                )

            # If face detected, take the largest bounding box
            if len(faces) > 0:
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest_face
                face_crop = frame[y:y + h, x:x + w]
                bbox = [int(x), int(y), int(w), int(h)]
                face_detected = True
            else:
                # If cascade did not find face, use a center crop as fallback
                h_img, w_img = frame.shape[:2]
                side = min(h_img, w_img)
                start_x = (w_img - side) // 2
                start_y = (h_img - side) // 2
                face_crop = frame[start_y:start_y + side, start_x:start_x + side]
                bbox = [int(start_x), int(start_y), int(side), int(side)]
                face_detected = False

            # Convert BGR (OpenCV) to RGB (PIL/PyTorch)
            face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
            img_tensor = self.transform(face_rgb).unsqueeze(0).to(self.device)

            with torch.no_grad():
                outputs = self.model(img_tensor)
                probs = torch.softmax(outputs, dim=1)
                confidence, pred = torch.max(probs, dim=1)
                conf_val = round(confidence.item(), 4)
                pred_idx = pred.item()
                all_probs = probs[0].cpu().numpy().tolist()

            emotion = EMOTION_MAP.get(pred_idx, "Neutral")
            prob_dict = {EMOTION_MAP[i]: round(all_probs[i], 4) for i in range(len(EMOTION_MAP))}

            return {
                "face_detected": face_detected,
                "emotion": emotion,
                "confidence": conf_val,
                "bbox": bbox,
                "probabilities": prob_dict,
                "source": "densenet121"
            }

        except Exception as e:
            print(f"[FaceEmotionDetector] Inference exception: {e}")
            return {"face_detected": False, "emotion": "Unknown", "confidence": 0.0, "error": str(e)}


# Global singleton instance
face_emotion_detector = FaceEmotionDetector()
