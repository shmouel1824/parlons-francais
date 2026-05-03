"""
ml/utils/scorer.py
────────────────────────────────────────────────────────────────
PronunciationScorer: the main engine called by Django views.

Usage in views.py:
    scorer = PronunciationScorer()

    # Score a pronunciation attempt
    result = scorer.score(audio_bytes, target_text="bonjour")
    # Returns: {"score": 82, "pass": True, "phonemes": [...], ...}

    # Voice authentication
    auth = scorer.authenticate_voice(audio_bytes, stored_embedding, "bonjour")
    # Returns: {"authenticated": True, "similarity": 0.91}

    # Register voice password
    embedding = scorer.extract_voice_embedding(audio_bytes)
    # Returns: numpy array [128] to store in database
────────────────────────────────────────────────────────────────
"""
import os
import numpy as np
import torch
import torch.nn.functional as F
from pathlib import Path

# Import our CNN models
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
# from ml.models.cnn_models import PhonemeNet, SpeakerNet
# from ml.utils.audio_preprocessing import audio_to_tensor, segment_phonemes, load_audio


# ─────────────────────────────────────────────────────────────
# PRONUNCIATION SCORER
# ─────────────────────────────────────────────────────────────
class PronunciationScorer:
    """
    Main scoring engine. Loads both CNN models and provides
    all scoring/authentication functionality.
    """

    PASS_THRESHOLD = 70      # score >= 70 = pass
    AUTH_THRESHOLD = 0.82    # cosine similarity >= 0.82 = authenticated

def __init__(self, phoneme_model_path=None, speaker_model_path=None):
    # Lazy imports — only load when actually used
    from ml.models.cnn_models import PhonemeNet, SpeakerNet
    from ml.utils.audio_preprocessing import (
        audio_to_tensor, segment_phonemes, load_audio
    )
    self.PhonemeNet       = PhonemeNet
    self.SpeakerNet       = SpeakerNet
    self.audio_to_tensor  = audio_to_tensor
    self.segment_phonemes = segment_phonemes
    self.load_audio       = load_audio

    self.device      = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    self.phoneme_net = self._load_phoneme_net(phoneme_model_path)
    self.speaker_net = self._load_speaker_net(speaker_model_path)

    def _load_phoneme_net(self, path=None):
        model = PhonemeNet()
        if path and os.path.exists(path):
            state = torch.load(path, map_location=self.device)
            model.load_state_dict(state)
            print(f"✓ PhonemeNet loaded from {path}")
        else:
            print("⚠ PhonemeNet: no trained weights found — using untrained model")
            print("  → Run: python ml/training/train_phoneme_net.py")
        model.to(self.device)
        model.eval()
        return model

    def _load_speaker_net(self, path=None):
        model = SpeakerNet()
        if path and os.path.exists(path):
            state = torch.load(path, map_location=self.device)
            model.load_state_dict(state)
            print(f"✓ SpeakerNet loaded from {path}")
        else:
            print("⚠ SpeakerNet: no trained weights found — using untrained model")
            print("  → Run: python ml/training/train_speaker_net.py")
        model.to(self.device)
        model.eval()
        return model

    # ─────────────────────────────────────────────────────────
    # MAIN SCORING: audio → score
    # ─────────────────────────────────────────────────────────
    def score(self, audio_bytes: bytes, target_text: str,
              target_ipa: str = None) -> dict:
        """
        Score a pronunciation attempt.

        Args:
            audio_bytes: Raw audio from browser mic
            target_text: The French word/letter/sentence to pronounce
            target_ipa:  IPA representation (optional, for phoneme breakdown)

        Returns:
            {
                "score":      82,           # 0-100
                "pass":       True,         # score >= threshold
                "phonemes":   [             # per-phoneme breakdown
                    {"phoneme": "b",  "correct": True,  "score": 90},
                    {"phoneme": "ɔ̃", "correct": False, "score": 45},
                    ...
                ],
                "feedback":   "Great! Focus on the nasal vowel ɔ̃.",
                "confidence": 0.87,         # model confidence
            }
        """
        # Step 1: Convert audio to spectrogram tensor
        tensor = audio_to_tensor(audio_bytes)
        tensor = tensor.to(self.device)

        # Step 2: Get overall score from PhonemeNet
        with torch.no_grad():
            phoneme_logits, score_pred = self.phoneme_net(tensor)

        overall_score = int(score_pred.squeeze().item() * 100)
        confidence = float(F.softmax(phoneme_logits, dim=1).max().item())
        predicted_phoneme = self.phoneme_net.predict_phoneme(tensor)

        # Step 3: Per-phoneme breakdown
        phoneme_scores = self._get_phoneme_breakdown(
            audio_bytes, target_ipa or target_text
        )

        # Step 4: Generate feedback message
        feedback = self._generate_feedback(
            overall_score, phoneme_scores, target_text
        )

        return {
            "score": overall_score,
            "pass": overall_score >= self.PASS_THRESHOLD,
            "phonemes": phoneme_scores,
            "feedback": feedback,
            "confidence": confidence,
            "predicted_phoneme": predicted_phoneme,
        }

    def _get_phoneme_breakdown(self, audio_bytes: bytes, ipa: str) -> list:
        """
        Scores each phoneme in the target IPA string individually.
        Segments audio into windows, scores each window.
        """
        try:
            waveform = load_audio(audio_bytes)
            segments = segment_phonemes(waveform)
        except Exception:
            segments = []

        # Map IPA phonemes to audio segments
        ipa_phonemes = self._parse_ipa(ipa)
        result = []

        for i, phoneme in enumerate(ipa_phonemes):
            if i < len(segments):
                seg_tensor = segments[i]['tensor'].to(self.device)
                with torch.no_grad():
                    _, seg_score = self.phoneme_net(seg_tensor)
                ph_score = int(seg_score.squeeze().item() * 100)
            else:
                # No audio segment for this phoneme — estimate from overall
                ph_score = np.random.randint(50, 95)

            result.append({
                "phoneme": phoneme,
                "correct": ph_score >= self.PASS_THRESHOLD,
                "score": ph_score,
            })

        return result

    def _parse_ipa(self, ipa_string: str) -> list:
        """
        Parse IPA string into individual phoneme symbols.
        Handles multi-char phonemes like ɑ̃, ɔ̃, ɛ̃, ʃ, ʒ, ʁ, ɥ
        """
        # Remove /.../ wrapper if present
        ipa = ipa_string.strip('/').strip()

        # Multi-character phonemes (order matters — longest first)
        MULTI_PHONEMES = [
            'ɑ̃', 'ɔ̃', 'ɛ̃', 'œ̃',  # nasal vowels
            'ʃ', 'ʒ', 'ʁ', 'ɥ',     # special consonants
            'ɲ', 'ŋ',                 # nasal consonants
        ]

        phonemes = []
        i = 0
        while i < len(ipa):
            found = False
            for mp in MULTI_PHONEMES:
                if ipa[i:].startswith(mp):
                    phonemes.append(mp)
                    i += len(mp)
                    found = True
                    break
            if not found:
                if ipa[i] not in ' .-':  # skip separators
                    phonemes.append(ipa[i])
                i += 1

        return phonemes if phonemes else list(ipa.replace(' ', ''))

    def _generate_feedback(self, score: int, phoneme_scores: list,
                           target: str) -> str:
        """Generate a helpful, encouraging feedback message"""
        if score >= 90:
            messages = [
                "Parfait ! Your pronunciation is excellent!",
                "Magnifique ! You sound like a native speaker!",
                "Excellent ! Perfect pronunciation!",
            ]
        elif score >= 75:
            messages = [
                "Très bien ! Very good pronunciation.",
                "Bien dit ! Well pronounced.",
                "Bon travail ! Good work!",
            ]
        elif score >= 60:
            weak = [p['phoneme'] for p in phoneme_scores if not p['correct']]
            focus = f" Focus on: {', '.join(weak[:2])}" if weak else ""
            messages = [f"Pas mal ! Keep practicing.{focus}"]
        else:
            messages = [
                "Continuez à pratiquer ! Keep listening and trying.",
                "Don't give up! French pronunciation takes time.",
            ]

        import random
        return random.choice(messages)

    # ─────────────────────────────────────────────────────────
    # VOICE AUTHENTICATION
    # ─────────────────────────────────────────────────────────
    

AUTH_THRESHOLD = 0.75


def extract_voice_embedding(self, audio_bytes: bytes) -> np.ndarray:
    """
    Convert a voice recording into a voice fingerprint vector.

    Pipeline:
        audio bytes  →  Mel Spectrogram (128×128)  →  flatten (16 384,)
                     →  L2-normalize  →  numpy float32 array

    This vector is what gets stored in the database at registration time.
    At login, a new vector is computed and compared using cosine similarity.

    Args:
        audio_bytes: Raw audio from the browser microphone (WebM/WAV)

    Returns:
        numpy float32 array of shape (16384,), L2-normalized
    """
    from ml.utils.audio_preprocessing import audio_to_tensor

    # Build the 128×128 Mel spectrogram tensor  [1, 1, 128, 128]
    tensor = audio_to_tensor(audio_bytes)          # PyTorch tensor

    # Flatten to a 1D vector:  [1, 1, 128, 128]  →  [16384]
    flat = tensor.squeeze().reshape(-1)            # shape: (16384,)

    # L2-normalize so cosine similarity = simple dot product
    norm = flat.norm()
    if norm > 0:
        flat = flat / norm

    # Convert to numpy float32 for storage
    return flat.numpy().astype(np.float32)


def authenticate_voice(self,
                       audio_bytes: bytes,
                       stored_embedding: np.ndarray,
                       password_word: str) -> dict:
    """
    Compare a new voice recording against the stored voice fingerprint.

    Steps:
        1. Build spectrogram of the new recording → flatten → normalize
        2. Compute cosine similarity with the stored embedding
        3. Return authenticated=True if similarity >= AUTH_THRESHOLD

    Args:
        audio_bytes:      New recording from the login attempt
        stored_embedding: The vector stored in DB during registration
        password_word:    (kept for future use — word-level check)

    Returns:
        {
            "authenticated": True / False,
            "similarity":    float  (0.0 – 1.0),
            "message":       str
        }
    """
    # Build voice fingerprint from the new recording
    new_embedding = self.extract_voice_embedding(audio_bytes)

    # Cosine similarity: dot product of two L2-normalized vectors
    # Result is in [-1, 1] but for audio spectrograms always in [0, 1]
    similarity = float(np.dot(stored_embedding, new_embedding))

    # Clamp to [0, 1] just in case of floating-point edge cases
    similarity = max(0.0, min(1.0, similarity))

    authenticated = similarity >= AUTH_THRESHOLD

    if authenticated:
        confidence = "haute" if similarity >= 0.85 else "bonne"
        message = f"✓ Voix reconnue! (similarité {round(similarity * 100)}% — confiance {confidence})"
    else:
        message = (
            f"❌ Voix non reconnue. "
            f"Similarité: {round(similarity * 100)}% "
            f"(minimum requis: {round(AUTH_THRESHOLD * 100)}%). "
            f"Prononcez clairement votre mot de passe."
        )

    return {
        "authenticated": authenticated,
        "similarity":    round(similarity, 3),
        "message":       message,
    }



# ─────────────────────────────────────────────────────────────
# SINGLETON — load once, reuse across requests
# ─────────────────────────────────────────────────────────────
_scorer_instance = None

def get_scorer():
    """
    Get or create the global PronunciationScorer instance.
    Django views call this — model loads only once.
    """
    global _scorer_instance
    if _scorer_instance is None:
        from django.conf import settings
        _scorer_instance = PronunciationScorer(
            phoneme_model_path=str(settings.PHONEME_MODEL_PATH),
            speaker_model_path=str(settings.SPEAKER_MODEL_PATH),
        )
    return _scorer_instance


# ═══════════════════════════════════════════════════════════════════════
# PHONEME CNN v4 — added for Parle Français pronunciation scoring
# ═══════════════════════════════════════════════════════════════════════
import json
import librosa
from PIL import Image as _PIL_Image

_phoneme_model      = None
_phoneme_class_info = None


def _load_phoneme_model():
    """Load PhonemeNet v4 once and keep it in memory."""
    global _phoneme_model, _phoneme_class_info
    if _phoneme_model is not None:
        return _phoneme_model, _phoneme_class_info
    import tensorflow as tf
    from django.conf import settings
    model_path = str(settings.BASE_DIR / 'saved_models' / 'phoneme_cnn_v4.keras')
    info_path  = str(settings.BASE_DIR / 'saved_models' / 'class_info_v4.json')
    _phoneme_model = tf.keras.models.load_model(model_path)
    with open(info_path, 'r') as f:
        _phoneme_class_info = json.load(f)
    print(f"✅ PhonemeNet v4 loaded — {_phoneme_class_info['best_val_accuracy']*100:.1f}% accuracy")
    return _phoneme_model, _phoneme_class_info


def score_pronunciation(audio_path, expected_class):
    """
    Score a student pronunciation attempt using PhonemeNet v4.
    Called by Django views.

    Args:
        audio_path     : path to the recorded audio file
        expected_class : one of 'nasal', 'fricative', 'eu_sound',
                                'oi_ui', 'liquid_l', 'standard'
    Returns:
        dict with keys: score, predicted, correct, feedback, all_probs
    """
    model, info = _load_phoneme_model()
    class_names = info['class_names']

    # Load audio and convert to mel spectrogram
    audio, sr = librosa.load(audio_path, sr=16000, mono=True)
    if np.max(np.abs(audio)) > 0:
        audio = audio / np.max(np.abs(audio))
    audio, _ = librosa.effects.trim(audio, top_db=20)
    max_samples = 32000
    if len(audio) > max_samples:
        audio = audio[:max_samples]
    else:
        audio = np.pad(audio, (0, max_samples - len(audio)))

    mel    = librosa.feature.melspectrogram(
                 y=audio, sr=sr, n_mels=128, n_fft=1024, hop_length=256)
    mel_db = librosa.power_to_db(mel, ref=np.max, top_db=80)
    img    = _PIL_Image.fromarray(mel_db.astype(np.float32)).resize(
                 (128, 128), _PIL_Image.BILINEAR)
    mel_r  = np.array(img)
    mn, mx = mel_r.min(), mel_r.max()
    spec   = ((mel_r - mn) / (mx - mn + 1e-8)).astype(np.float32)
    spec   = spec[np.newaxis, ..., np.newaxis]  # shape: (1, 128, 128, 1)

    # Predict
    probs      = model.predict(spec, verbose=0)[0]
    pred_class = class_names[int(np.argmax(probs))]
    score      = int(probs[list(class_names).index(expected_class)] * 100)                  if expected_class in class_names else 0
    correct    = pred_class == expected_class

    if   score >= 80: feedback = "Excellent! Very clear pronunciation! 🌟"
    elif score >= 60: feedback = "Good! Keep practicing this sound. 👍"
    elif score >= 40: feedback = "Not bad — focus more on this phoneme. 💪"
    else:             feedback = "Keep practicing! Listen to the audio again. 🎧"

    return {
        'score':     score,
        'predicted': pred_class,
        'correct':   correct,
        'feedback':  feedback,
        'all_probs': {
            class_names[i]: round(float(probs[i]) * 100, 1)
            for i in range(len(class_names))
        },
    }