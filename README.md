# 🇫🇷 Parle Français — French Pronunciation Learning App

AI-powered French language learning using CNN Deep Learning.

---

## Architecture Overview

```
parle_francais/
├── parle_francais/          Django project config
│   ├── settings.py          Configuration + ML model paths
│   └── urls.py              Main URL routing
│
├── core/                    Main Django app
│   ├── models.py            Database: User, Exercise, Progress, Attempts
│   ├── views.py             Page views + JSON API endpoints
│   ├── urls.py              URL patterns
│   ├── templates/core/      HTML templates (extend base.html)
│   │   ├── base.html        Sidebar layout shell
│   │   ├── home.html        Dashboard
│   │   ├── alphabet.html    Alphabet module
│   │   ├── phonemes.html    Phonème groups
│   │   ├── words.html       Vocabulary
│   │   ├── sentences.html   Full sentences
│   │   ├── quiz.html        EN/HE → FR quiz
│   │   ├── dictee.html      Listening exercise
│   │   ├── stats.html       Personal statistics
│   │   └── auth/login.html  Voice login/register
│   └── static/core/
│       ├── css/style.css    Global styles
│       └── js/app.js        MicRecorder, VoiceAuth, TTS
│
└── ml/                      Deep Learning pipeline
    ├── models/
    │   └── cnn_models.py    PhonemeNet + SpeakerNet CNN definitions
    ├── utils/
    │   ├── audio_preprocessing.py  Audio → Mel Spectrogram → Tensor
    │   └── scorer.py               PronunciationScorer (called by views)
    └── training/
        ├── train_phoneme_net.py    Training script for PhonemeNet
        └── train_speaker_net.py   Training script for SpeakerNet (TODO)
```

---

## The Two CNN Models

### 1. PhonemeNet — Pronunciation Scorer
```
Input:  Mel Spectrogram [1, 128, 128]
        (your voice recording turned into an image)
        
CNN:    Conv(1→32) → Conv(32→64) → Conv(64→128) → Conv(128→256)
        each block: Conv2D → BatchNorm → ReLU → MaxPool
        
Output: ┌─ Phoneme class (which of 37 French phonemes?)
        └─ Quality score (0.0 to 1.0 = 0% to 100%)
```

### 2. SpeakerNet — Voice Authentication
```
Input:  Mel Spectrogram [1, 128, 128]

CNN:    Same 4 conv blocks

Output: 128-dim voice embedding (your "voice fingerprint")
        L2-normalized for cosine similarity comparison

Login:  cosine_similarity(stored_embedding, new_embedding) ≥ 0.82 → ✓
```

---

## Data Flow: Recording to Score

```
Browser mic → MediaRecorder → WebM audio blob
    ↓
POST /api/score/ (with CSRF token)
    ↓
Django view receives audio file
    ↓
audio_preprocessing.py:
    - Load audio (librosa)
    - Resample to 16kHz
    - Normalize + trim silence
    - Compute Mel Spectrogram [128 × T]
    - Resize to [128 × 128]
    - Convert to PyTorch tensor [1, 1, 128, 128]
    ↓
PhonemeNet CNN:
    - Feature extraction (4 conv blocks)
    - Global Average Pool
    - Two heads: phoneme class + quality score
    ↓
JSON response: { score: 82, pass: true, phonemes: [...] }
    ↓
JavaScript showScore() → update UI
```

---

## Setup Instructions

```bash
# 1. Clone / create project
cd parle_francais

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py makemigrations
python manage.py migrate

# 5. Load initial data (letters, phonemes, words)
python manage.py loaddata core/fixtures/initial_data.json

# 6. Create admin user
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver

# Visit: http://localhost:8000
```

---

## Training the CNN Models

```bash
# Step 1: Download data
# Mozilla Common Voice FR: https://commonvoice.mozilla.org/fr/datasets
# Extract to: ml/data/cv-corpus-fr/

# Step 2: Prepare phoneme dataset
python ml/training/prepare_data.py

# Step 3: Train PhonemeNet
python ml/training/train_phoneme_net.py
# Takes ~2-4 hours on GPU, ~1-2 days on CPU
# Model saved to: ml/models/phoneme_cnn.pth

# Step 4: Train SpeakerNet
python ml/training/train_speaker_net.py
# Model saved to: ml/models/speaker_cnn.pth
```

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/score/` | Score pronunciation attempt |
| POST | `/api/voice/login/` | Authenticate with voice |
| POST | `/api/voice/register/` | Register voice password |
| POST | `/api/feedback/` | User feedback on score |
| POST | `/api/dictee/` | Submit dictée answer |

---

## French Phonemes Taught (37 total)

| Category | Phonemes |
|----------|---------|
| Oral vowels | a, e, ɛ, i, o, ɔ, u, y, ø, œ, ə |
| **Nasal vowels** ⭐ | **ɑ̃, ɔ̃, ɛ̃, œ̃** |
| Semi-vowels | j, w, **ɥ** |
| Plosives | p, b, t, d, k, ɡ |
| Fricatives | f, v, s, z, **ʃ, ʒ** |
| Nasals | m, n, **ɲ**, ŋ |
| Liquids | l, **ʁ** |

Bold = sounds that don't exist in English/Hebrew → hardest to learn!

---

## Next Steps

- [ ] Complete all HTML templates (home, alphabet, words, stats...)
- [ ] Download and prepare training data
- [ ] Train PhonemeNet (Phase 1: clean data)
- [ ] Train SpeakerNet (voice embeddings)
- [ ] Add more word categories (animals, travel, family...)
- [ ] Add gamification (badges, leaderboard)
- [ ] Mobile-responsive design
- [ ] Deployment (Heroku / DigitalOcean)
