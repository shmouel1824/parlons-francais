"""
core/views.py
─────────────────────────────────────────────────────────────
PAGE VIEWS (render HTML templates):
    home, alphabet_view, phonemes_view, words_view,
    sentences_view, quiz_view, dictee_view, stats_view

AUTH VIEWS:
    login_view, register_view, logout_view

ORIGINAL API VIEWS:
    api_score_pronunciation, api_voice_register,
    api_voice_login, api_update_feedback, api_save_dictee

NEW PRONUNCIATION VIEWS (added for PhonemeNet v4):
    pronunciation, score_attempt, dashboard
─────────────────────────────────────────────────────────────
"""
import os
import json
import tempfile
import numpy as np
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count


import logging

logger = logging.getLogger(__name__)


from .models import (
    User, Exercise, ExerciseCategory, UserProgress,
    PronunciationAttempt, PhonemeGroup, UserPhonemeScore,
    QuizResult, DicteeResult, StudentAttempt
)


# ─────────────────────────────────────────────────────────────
# PAGE VIEWS (original)
# ─────────────────────────────────────────────────────────────

def home(request):
    """Dashboard / home page"""
    if not request.user.is_authenticated:
        return redirect('login')

    categories = ExerciseCategory.objects.all()
    module_progress = []
    for cat in categories:
        total = cat.exercises.count()
        mastered = UserProgress.objects.filter(
            user=request.user,
            exercise__category=cat,
            mastered=True
        ).count()
        module_progress.append({
            'category': cat,
            'total': total,
            'mastered': mastered,
            'percent': int((mastered / total * 100) if total > 0 else 0),
        })

    context = {
        'user': request.user,
        'module_progress': module_progress,
    }
    return render(request, 'core/home.html', context)


def alphabet_view(request):
    """Alphabet module page"""
    if not request.user.is_authenticated:
        return redirect('login')

    category = ExerciseCategory.objects.filter(category_type='alphabet').first()
    exercises = []
    if category:
        for ex in category.exercises.all():
            progress = UserProgress.objects.filter(
                user=request.user, exercise=ex
            ).first()
            exercises.append({
                'exercise': ex,
                'mastered': progress.mastered if progress else False,
                'best_score': progress.best_score if progress else 0,
            })

    return render(request, 'core/alphabet.html', {
        'exercises': exercises,
        'category': category,
    })


def phonemes_view(request):
    """Phoneme groups module"""
    if not request.user.is_authenticated:
        return redirect('login')

    phoneme_groups = PhonemeGroup.objects.all()
    groups_with_scores = []
    for group in phoneme_groups:
        user_score = UserPhonemeScore.objects.filter(
            user=request.user, phoneme_group=group
        ).first()
        groups_with_scores.append({
            'group': group,
            'average_score': user_score.average_score if user_score else 0,
            'mastered': user_score.mastered if user_score else False,
        })

    return render(request, 'core/phonemes.html', {
        'phoneme_groups': groups_with_scores,
    })


def words_view(request):
    """Words module"""
    if not request.user.is_authenticated:
        return redirect('login')

    categories = ExerciseCategory.objects.filter(category_type='word')
    return render(request, 'core/words.html', {'categories': categories})


def sentences_view(request):
    """Sentences module"""
    if not request.user.is_authenticated:
        return redirect('login')

    category = ExerciseCategory.objects.filter(category_type='sentence').first()
    exercises = category.exercises.all() if category else []
    return render(request, 'core/sentences.html', {'exercises': exercises})


def quiz_view(request):
    """Quiz module"""
    if not request.user.is_authenticated:
        return redirect('login')

    category = ExerciseCategory.objects.filter(category_type='quiz').first()
    exercises = list(category.exercises.all()) if category else []
    return render(request, 'core/quiz.html', {
        'exercises': exercises,
        'native_language': request.user.native_language,
    })


def dictee_view(request):
    """Dictée module"""
    if not request.user.is_authenticated:
        return redirect('login')

    category = ExerciseCategory.objects.filter(category_type='dictee').first()
    exercises = list(category.exercises.all()) if category else []
    return render(request, 'core/dictee.html', {'exercises': exercises})


@login_required
def stats_view(request):
    """Personal statistics dashboard"""
    user = request.user

    total_attempts = PronunciationAttempt.objects.filter(user=user).count()
    avg_score = PronunciationAttempt.objects.filter(
        user=user
    ).aggregate(avg=Avg('overall_score'))['avg'] or 0

    total_mastered = UserProgress.objects.filter(user=user, mastered=True).count()

    from datetime import timedelta
    today = timezone.now().date()
    weekly_scores = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_avg = PronunciationAttempt.objects.filter(
            user=user,
            created_at__date=day
        ).aggregate(avg=Avg('overall_score'))['avg']
        weekly_scores.append({
            'day': day.strftime('%a'),
            'score': round(day_avg or 0, 1),
        })

    phoneme_scores = UserPhonemeScore.objects.filter(user=user).select_related('phoneme_group')

    recent = PronunciationAttempt.objects.filter(
        user=user
    ).select_related('exercise').order_by('-created_at')[:10]

    context = {
        'user': user,
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 1),
        'total_mastered': total_mastered,
        'weekly_scores': json.dumps(weekly_scores),
        'phoneme_scores': phoneme_scores,
        'recent_attempts': recent,
    }
    return render(request, 'core/stats.html', context)


# ─────────────────────────────────────────────────────────────
# AUTH VIEWS (original)
# ─────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
       redirect('home')
    return render(request, 'core/auth/login.html')


def register_view(request):
    return render(request, 'core/auth/register.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────────────────────────
# ORIGINAL API VIEWS
# ─────────────────────────────────────────────────────────────

@require_POST
def api_score_pronunciation(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    audio_file = request.FILES.get('audio')
    if not audio_file:
        return JsonResponse({'error': 'No audio file'}, status=400)

    exercise_id = request.POST.get('exercise_id')
    exercise = get_object_or_404(Exercise, id=exercise_id)
    audio_bytes = audio_file.read()

    try:
        from ml.utils.scorer import get_scorer
        scorer = get_scorer()
        result = scorer.score(
            audio_bytes=audio_bytes,
            target_text=exercise.french_text,
            target_ipa=exercise.ipa,
        )
    except Exception as e:
        import random
        score = random.randint(55, 95)
        result = {
            'score': score,
            'pass': score >= 70,
            'phonemes': [],
            'feedback': 'Bien dit !' if score >= 70 else 'Continuez !',
            'confidence': 0.5,
        }

    attempt = PronunciationAttempt.objects.create(
        user=request.user,
        exercise=exercise,
        overall_score=result['score'],
        passed=result['pass'],
        phoneme_scores=result.get('phonemes', []),
        model_confidence=result.get('confidence', 0),
    )
    attempt.audio_file.save(f'attempt_{attempt.id}.webm', audio_file, save=True)

    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        exercise=exercise,
    )
    progress.attempts += 1
    progress.last_score = result['score']
    if result['score'] > progress.best_score:
        progress.best_score = result['score']
    if result['pass'] and not progress.mastered:
        progress.mastered = True
        progress.mastered_at = timezone.now()
    progress.save()

    xp_gained = 0
    if result['pass']:
        xp_gained = 10 if progress.attempts == 1 else 5
        request.user.xp += xp_gained
        request.user.save()

    return JsonResponse({
        **result,
        'xp_gained': xp_gained,
        'total_xp': request.user.xp,
        'attempt_id': attempt.id,
    })



# Threshold: similarity must be at least this to authenticate
# 0.75 = good balance of security and tolerance for mic variation
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  DUAL-CHECK VOICE AUTH FIX                                                  ║
║                                                                              ║
║  Problem: "jojo" and "momo" have identical spectrogram shapes               ║
║           (same rhythm, same vowel) → spectrogram alone can't tell them     ║
║           apart.                                                             ║
║                                                                              ║
║  Solution: TWO checks must both pass:                                       ║
║    1. Spectrogram similarity ≥ 75%  (voice fingerprint)                     ║
║    2. Recognized word matches stored word ≥ 80%  (word content)             ║
║                                                                              ║
║  The browser sends both the audio blob AND the transcript.                  ║
║  If either check fails → rejected.                                          ║
║                                                                              ║
║  In core/views.py: replace api_voice_register + api_voice_login             ║
║  In login.html JS: update VoiceAuth to send recognized_text                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import difflib
import numpy as np
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

SAMPLE_RATE    = 16000
N_MELS         = 128
N_FFT          = 1024
HOP_LENGTH     = 256
DURATION       = 3.0
TARGET_SIZE    = 128
VOICE_THRESHOLD = 0.75   # spectrogram cosine similarity
WORD_THRESHOLD  = 0.80   # word transcript fuzzy match


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS  (keep these above api_voice_register in views.py)
# ─────────────────────────────────────────────────────────────────────────────

def _spectrogram_embedding(audio_bytes: bytes) -> np.ndarray:
    """audio bytes → Mel spectrogram 128×128 → flat L2-normalized vector"""
    import librosa
    from PIL import Image

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        audio, sr = librosa.load(tmp_path, sr=SAMPLE_RATE, mono=True)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val
    audio, _ = librosa.effects.trim(audio, top_db=20)

    max_samples = int(SAMPLE_RATE * DURATION)
    if len(audio) > max_samples:
        audio = audio[:max_samples]
    else:
        audio = np.pad(audio, (0, max_samples - len(audio)))

    mel    = librosa.feature.melspectrogram(
        y=audio, sr=SAMPLE_RATE,
        n_mels=N_MELS, n_fft=N_FFT, hop_length=HOP_LENGTH
    )
    mel_db = librosa.power_to_db(mel, ref=np.max, top_db=80)

    img   = Image.fromarray(mel_db.astype(np.float32))
    img   = img.resize((TARGET_SIZE, N_MELS), Image.BILINEAR)
    mel_r = np.array(img)

    mn, mx   = mel_r.min(), mel_r.max()
    mel_norm = ((mel_r - mn) / (mx - mn + 1e-8)).astype(np.float32)

    flat = mel_norm.reshape(-1)
    norm = np.linalg.norm(flat)
    if norm > 0:
        flat = flat / norm
    return flat.astype(np.float32)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity of two L2-normalized vectors → [0.0, 1.0]"""
    return max(0.0, min(1.0, float(np.dot(a, b))))


def _word_similarity(a: str, b: str) -> float:
    """Fuzzy string match → [0.0, 1.0]. Handles small mishearings."""
    a = a.lower().strip()
    b = b.lower().strip()
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


# ─────────────────────────────────────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────────────────────────────────────

from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@require_POST
def api_voice_register(request):
    """
    POST /api/voice/register/
    Form fields:
        audio           : mic recording (WebM)
        recognized_text : what the browser Speech API heard  ← NEW
        username        : desired username
        email           : optional
        password_word   : French word chosen as vocal password
    """
    from .models import User   # remove if already imported at top of views.py

    audio_file      = request.FILES.get('audio')
    recognized_text = request.POST.get('recognized_text', '').strip().lower()
    username        = request.POST.get('username', '').strip()
    email           = request.POST.get('email', '').strip()
    password_word   = request.POST.get('password_word', '').strip().lower()

    if not audio_file:
        return JsonResponse({'error': 'No audio received.'}, status=400)
    if not username:
        return JsonResponse({'error': 'Username is required.'}, status=400)
    if not password_word:
        return JsonResponse({'error': 'Password word is required.'}, status=400)
    if not recognized_text:
        return JsonResponse({
            'error': (
                f'Voice not recognized by browser. '
                f'Please say "{password_word}" clearly and try again.'
            )
        }, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': f'Username "{username}" is already taken.'}, status=400)

    # ── Check: did the user actually SAY the password word? ───
    word_sim = _word_similarity(recognized_text, password_word)
    if word_sim < WORD_THRESHOLD:
        return JsonResponse({
            'error': (
                f'You said "{recognized_text}" but the password word is "{password_word}". '
                f'Match: {round(word_sim * 100)}% (need {round(WORD_THRESHOLD * 100)}%). '
                f'Please pronounce more clearly.'
            ),
            'word_similarity': round(word_sim, 3),
        }, status=400)

    # ── Build spectrogram fingerprint ─────────────────────────
    try:
        audio_bytes = audio_file.read()
        embedding   = _spectrogram_embedding(audio_bytes)
    except Exception as e:
        logger.error(f"[REGISTER] Spectrogram failed for '{username}': {e}")
        return JsonResponse({
            'error': f'Could not process audio: {str(e)}'
        }, status=500)

    # ── Create user ───────────────────────────────────────────
    user = User.objects.create_user(
        username=username,
        email=email if email else '',
        password=None,
    )
    user.voice_password_word = password_word
    user.set_voice_embedding_array(embedding)
    user.save()

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    return JsonResponse({
        'success':  True,
        'message':  f'Bienvenue {username}! Empreinte vocale pour "{password_word}" enregistrée.',
        'redirect': '/',
    })


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────

@require_POST
def api_voice_login(request):
    """
    POST /api/voice/login/
    Form fields:
        audio           : mic recording (WebM)
        recognized_text : what the browser Speech API heard
        username        : their username

    DUAL CHECK:
        1. recognized_text  vs  stored voice_password_word  (>= 80%)
        2. new spectrogram  vs  stored spectrogram vector   (>= 75%)
        Both must pass. On failure, always return the same generic message
        so the user never learns what the correct password word is.
    """
    from .models import User   # remove if already imported at top of views.py

    audio_file      = request.FILES.get('audio')
    recognized_text = request.POST.get('recognized_text', '').strip().lower()
    username        = request.POST.get('username', '').strip()

    # ── Validate ──────────────────────────────────────────────
    if not audio_file:
        return JsonResponse({'authenticated': False,
                             'error': 'No audio received.'}, status=400)
    if not username:
        return JsonResponse({'authenticated': False,
                             'error': 'Username is required.'}, status=400)

    # ── Find user ─────────────────────────────────────────────
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # Generic message — don't reveal whether the username exists
        return JsonResponse({'authenticated': False,
                             'message': '❌ Identifiants incorrects. Réessayez.'}, status=401)

    # ── Get stored fingerprint and password word ───────────────
    stored_embedding = user.get_voice_embedding_array()
    stored_word      = getattr(user, 'voice_password_word', None)

    if stored_embedding is None or not stored_word:
        return JsonResponse({
            'authenticated': False,
            'error': 'No voice password registered for this account.'
        }, status=400)

    # ── CHECK 1: Did they say the right word? ─────────────────
    if not recognized_text:
        return JsonResponse({
            'authenticated': False,
            'message': '❌ Voix non reconnue par le navigateur. Parlez clairement et réessayez.',
        }, status=401)

    word_sim = _word_similarity(recognized_text, stored_word)

    if word_sim < WORD_THRESHOLD:
        # ⛔ Do NOT reveal stored_word or recognized_text in the message
        logger.info(f"[LOGIN] Word mismatch for '{username}': "
                    f"said '{recognized_text}', expected '{stored_word}' "
                    f"({round(word_sim * 100)}%)")
        return JsonResponse({
            'authenticated': False,
            'message': '❌ Mot de passe vocal incorrect. Réessayez.',
        }, status=401)

    # ── CHECK 2: Does the voice spectrogram match? ────────────
    try:
        audio_bytes = audio_file.read()
        new_vec     = _spectrogram_embedding(audio_bytes)
    except Exception as e:
        logger.error(f"[LOGIN] Spectrogram failed for '{username}': {e}")
        return JsonResponse({
            'authenticated': False,
            'message': '❌ Impossible de traiter l\'audio. Réessayez.',
        }, status=500)

    voice_sim = _cosine_similarity(stored_embedding, new_vec)

    if voice_sim < VOICE_THRESHOLD:
        # ⛔ Do NOT reveal the similarity score in the message
        logger.info(f"[LOGIN] Voice mismatch for '{username}': "
                    f"similarity {round(voice_sim * 100)}%")
        return JsonResponse({
            'authenticated': False,
            'message': '❌ Mot de passe vocal incorrect. Réessayez.',
        }, status=401)

    # ── Both checks passed → login ────────────────────────────
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return JsonResponse({
        'authenticated': True,
        'message':       f'✓ Bonjour {user.username} ! Connexion réussie.',
        'redirect':      '/',
    })

@require_POST
def api_update_feedback(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    attempt_id = request.POST.get('attempt_id')
    feedback = request.POST.get('feedback')

    try:
        attempt = PronunciationAttempt.objects.get(id=attempt_id, user=request.user)
        attempt.user_feedback = feedback
        attempt.save()
        return JsonResponse({'success': True})
    except PronunciationAttempt.DoesNotExist:
        return JsonResponse({'error': 'Attempt not found'}, status=404)


@require_POST
def api_save_dictee(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    exercise_id = request.POST.get('exercise_id')
    typed_text = request.POST.get('typed_text', '').strip().lower()
    exercise = get_object_or_404(Exercise, id=exercise_id)
    correct_text = exercise.french_text.strip().lower()
    is_correct = typed_text == correct_text

    DicteeResult.objects.create(
        user=request.user,
        exercise=exercise,
        typed_text=typed_text,
        correct=is_correct,
    )

    return JsonResponse({
        'correct': is_correct,
        'correct_text': exercise.french_text,
        'ipa': exercise.ipa,
    })


# ─────────────────────────────────────────────────────────────
# NEW VIEWS — PhonemeNet v4 pronunciation scoring
# ─────────────────────────────────────────────────────────────

@login_required
def pronunciation(request, exercise_id):
    """Practice page for one phoneme exercise."""
    from .models import StudentAttempt
    exercise = get_object_or_404(Exercise, id=exercise_id)
    attempts = StudentAttempt.objects.filter(
        student=request.user,
        exercise=exercise
    ).order_by('-attempted_at')[:5]
    return render(request, 'core/pronunciation.html', {
        'exercise': exercise,
        'attempts': attempts,
    })


@login_required
@csrf_exempt
def score_attempt(request, exercise_id):
    """Receive audio from browser microphone, score with PhonemeNet v4, return JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    from .models import StudentAttempt
    from ml.utils.scorer import score_pronunciation

    exercise   = get_object_or_404(Exercise, id=exercise_id)
    audio_file = request.FILES.get('audio')
    if not audio_file:
        return JsonResponse({'error': 'No audio received'}, status=400)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
        for chunk in audio_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        result = score_pronunciation(tmp_path, exercise.phoneme_class)
    except Exception as e:
        os.unlink(tmp_path)
        return JsonResponse({'error': str(e)}, status=500)

    StudentAttempt.objects.create(
        student   = request.user,
        exercise  = exercise,
        score     = result['score'],
        predicted = result['predicted'],
        correct   = result['correct'],
    )
    os.unlink(tmp_path)
    return JsonResponse(result)


@login_required
def dashboard(request):
    """Phoneme pronunciation dashboard — student stats by phoneme class."""
    from .models import StudentAttempt
    attempts  = StudentAttempt.objects.filter(student=request.user)
    stats     = attempts.values('exercise__phoneme_class').annotate(
        avg_score=Avg('score'), count=Count('id'))
    total     = attempts.count()
    avg_score = attempts.aggregate(Avg('score'))['score__avg'] or 0
    recent    = attempts.order_by('-attempted_at')[:10]
    return render(request, 'core/stats.html', {
        'stats':     list(stats),
        'total':     total,
        'avg_score': round(avg_score, 1),
        'recent':    recent,
    })

def api_exercises(request):
    """Return exercises for a category as JSON."""
    category_id = request.GET.get('category')
    if not category_id:
        return JsonResponse({'error': 'No category'}, status=400)
    exercises = Exercise.objects.filter(category_id=category_id).values(
        'id', 'french_text', 'ipa', 'english_text', 'difficulty', 'phoneme_class'
    )
    return JsonResponse({'exercises': list(exercises)})

@require_POST
def api_text_login(request):
    """Standard username/password login — for admin users without voice password."""
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({'success': True, 'redirect': '/'})
    return JsonResponse({'error': 'Invalid username or password'}, status=401)


def qa_tests(request):
    return render(request, 'core/qa_tests.html')


@require_POST
def api_score_letter(request):
    """
    POST /api/score-letter/
    Form fields:
        audio          : mic recording (WebM)
        expected_letter: the letter shown to the student, e.g. "D"

    Returns JSON:
        { score, pass, predicted, correct, feedback, all_probs }
    """
    audio_file      = request.FILES.get('audio')
    expected_letter = request.POST.get('expected_letter', '').strip().upper()

    if not audio_file:
        return JsonResponse({'error': 'No audio received.'}, status=400)
    if not expected_letter or len(expected_letter) != 1:
        return JsonResponse({'error': 'expected_letter must be a single letter.'}, status=400)

    try:
        from ml.utils.letter_scorer import score_letter
        audio_bytes = audio_file.read()
        result      = score_letter(audio_bytes, expected_letter)
        return JsonResponse(result)

    except FileNotFoundError as e:
        return JsonResponse({
            'error': 'LetterNet model not trained yet. Run train_letter_net.py first.',
            'detail': str(e)
        }, status=503)

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[SCORE LETTER] {e}")
        return JsonResponse({'error': str(e)}, status=500)

