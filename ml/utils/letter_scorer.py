"""
ADD THIS to ml/utils/scorer.py
— or keep it as a separate file ml/utils/letter_scorer.py

This scores a letter pronunciation attempt using LetterNet.
Call it from the alphabet page API endpoint.
"""

import os
import json
import tempfile
import numpy as np
import librosa
from pathlib import Path
from PIL import Image

# ── Load model once (singleton) ──────────────────────────────
_letter_model = None
_letter_info  = None

def _load_letter_model():
    global _letter_model, _letter_info

    if _letter_model is not None:
        return _letter_model, _letter_info

    import tensorflow as tf

    base     = Path(__file__).resolve().parent.parent.parent / 'saved_models'
    model_path = base / 'letter_cnn_best.keras'
    info_path  = base / 'letter_info.json'

    if not model_path.exists():
        raise FileNotFoundError(
            f"LetterNet model not found at {model_path}\n"
            f"Run: python train_letter_net.py"
        )

    _letter_model = tf.keras.models.load_model(str(model_path))

    with open(info_path) as f:
        _letter_info = json.load(f)

    print(f"✓ LetterNet loaded — {_letter_info['num_classes']} letters, "
          f"val accuracy: {_letter_info['val_accuracy']}%")

    return _letter_model, _letter_info


# ── Audio → spectrogram (same pipeline as training) ──────────
def _audio_to_spec(audio, sr=16000):
    mx = np.max(np.abs(audio))
    if mx > 0:
        audio = audio / mx

    audio, _ = librosa.effects.trim(audio, top_db=20)

    max_samples = int(sr * 2.0)   # 2 seconds (same as training DURATION)
    if len(audio) > max_samples:
        start = (len(audio) - max_samples) // 2
        audio = audio[start:start + max_samples]
    else:
        audio = np.pad(audio, (0, max_samples - len(audio)))

    mel    = librosa.feature.melspectrogram(
        y=audio, sr=sr, n_mels=128, n_fft=1024, hop_length=256
    )
    mel_db = librosa.power_to_db(mel, ref=np.max, top_db=80)

    img   = Image.fromarray(mel_db.astype(np.float32))
    img   = img.resize((128, 128), Image.BILINEAR)
    mel_r = np.array(img)

    mn, mx = mel_r.min(), mel_r.max()
    spec   = ((mel_r - mn) / (mx - mn + 1e-8)).astype(np.float32)
    return spec[np.newaxis, ..., np.newaxis]   # shape: (1, 128, 128, 1)


# ── MAIN FUNCTION — call this from views.py ──────────────────
def score_letter(audio_bytes: bytes, expected_letter: str) -> dict:
    """
    Score a letter pronunciation attempt.

    Args:
        audio_bytes    : raw audio from browser mic (WebM)
        expected_letter: the letter that was shown to the student, e.g. "D"

    Returns:
        {
            "score":     85,          # 0-100
            "pass":      True,        # score >= 70
            "predicted": "D",         # what the model thinks was said
            "correct":   True,        # predicted == expected
            "feedback":  "Excellent!",
            "all_probs": {"A": 2.1, "B": 1.3, "D": 85.0, ...}
        }
    """
    expected_letter = expected_letter.upper().strip()

    # ── Write audio to temp file (librosa needs file extension) ──
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        audio, _ = librosa.load(tmp_path, sr=16000, mono=True)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    # ── Spectrogram ───────────────────────────────────────────
    spec = _audio_to_spec(audio)

    # ── Predict ───────────────────────────────────────────────
    model, info = _load_letter_model()
    class_names = info['class_names']   # ['A','B','C',...,'Z']

    probs      = model.predict(spec, verbose=0)[0]
    pred_idx   = int(np.argmax(probs))
    pred_letter = class_names[pred_idx]

    # Score = confidence that it IS the expected letter (0-100)
    if expected_letter in class_names:
        exp_idx = class_names.index(expected_letter)
        score   = int(probs[exp_idx] * 100)
    else:
        score = 0

    correct = (pred_letter == expected_letter)

    # ── Feedback ──────────────────────────────────────────────
    if correct and score >= 80:
        feedback = f"Excellent! Parfait pour la lettre {expected_letter}! 🌟"
    elif correct and score >= 60:
        feedback = f"Bien! La lettre {expected_letter} est reconnue. 👍"
    elif not correct and score >= 30:
        feedback = f"Presque! Le modèle entend '{pred_letter}'. Réessayez. 💪"
    else:
        feedback = f"Écoutez encore la lettre {expected_letter} et réessayez. 🎧"

    return {
        'score':     score,
        'pass':      score >= 70,
        'predicted': pred_letter,
        'correct':   correct,
        'feedback':  feedback,
        'all_probs': {
            class_names[i]: round(float(probs[i]) * 100, 1)
            for i in range(len(class_names))
        },
    }