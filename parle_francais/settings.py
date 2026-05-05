"""
Parle Français — Django Settings (TensorFlow version)
"""
import dj_database_url
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', '%^x^r1xi@94ppqrxws$n2x9kax*4&!v(hc(q=)nyjoxgs&@pm7')
# a8gkf3lvox55ysn^aw=y(4w#dzwk3$++8@*9iz!k=waa(m1(hf
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'parle_francais.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],          # templates live inside core/templates/
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'parle_francais.wsgi.application'

# ── Database ─────────────────────────────────────────────────


DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600
    )
}

# ── Custom User Model ────────────────────────────────────────
AUTH_USER_MODEL = 'core.User'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# ── Static & Media files ─────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Default primary key ──────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── ML Model paths (TensorFlow .keras / .h5) ─────────────────
ML_MODELS_DIR        = BASE_DIR / 'ml' / 'models'
PHONEME_MODEL_PATH   = ML_MODELS_DIR / 'phoneme_cnn.keras'
SPEAKER_MODEL_PATH   = ML_MODELS_DIR / 'speaker_cnn.keras'

# ── Pronunciation thresholds ─────────────────────────────────
PRONUNCIATION_PASS_THRESHOLD = 70    # score >= 70 = pass
VOICE_AUTH_THRESHOLD         = 0.82  # cosine similarity >= 0.82 = authenticated

# ── Audio settings ───────────────────────────────────────────
AUDIO_SAMPLE_RATE = 16000
MEL_N_MELS        = 128
MEL_N_FFT         = 1024
MEL_HOP_LENGTH    = 256

import os
MEDIA_URL  = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


JAZZMIN_SETTINGS = {
    "site_title":        "Parle Français Admin",
    "site_header":       "Parle Français",
    "site_brand":        "🇫🇷 Parle Français",
    "site_icon":         None,
    "site_url": "/", 
    "welcome_sign":      "Bienvenue dans l'administration",
    "copyright":         "Parle Français",
    "theme":             "darkly",
    "dark_mode_theme":   "darkly",
    "button_classes": {
        "primary":   "btn-primary",
        "secondary": "btn-secondary",
        "info":      "btn-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },
    "topmenu_links": [
        {"name": "Home",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Back to Site", "url": "/", "new_window": False}, # <--- This is the magic button
    ],
    "icons": {
        "core.User":               "fas fa-users",
        "core.Exercise":           "fas fa-book",
        "core.ExerciseCategory":   "fas fa-folder",
        "core.PronunciationAttempt": "fas fa-microphone",
        "core.StudentAttempt":     "fas fa-chart-bar",
        "core.PhonemeGroup":       "fas fa-music",
        "auth.Group":              "fas fa-shield-alt",
    },
}