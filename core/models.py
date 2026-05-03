"""
core/models.py
All database models for Parle Français
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
import numpy as np
import json


# ─────────────────────────────────────────────────────────────
# CUSTOM USER MODEL
# ─────────────────────────────────────────────────────────────
class User(AbstractUser):
    """
    Extends Django's built-in User.
    Adds voice embedding for pronunciation-based login.
    """
    voice_password_word = models.CharField(
        max_length=100, blank=True,
        help_text="The French word used as voice password"
    )
    voice_embedding = models.TextField(
        blank=True,
        help_text="JSON array: 128-dim speaker embedding vector"
    )
    level              = models.IntegerField(default=1)
    xp                 = models.IntegerField(default=0)
    streak_days        = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    native_language    = models.CharField(
        max_length=10,
        choices=[('en','English'),('he','Hebrew'),('ar','Arabic'),('other','Other')],
        default='en'
    )

    def get_voice_embedding_array(self):
        if self.voice_embedding:
            return np.array(json.loads(self.voice_embedding))
        return None

    def set_voice_embedding_array(self, arr):
        self.voice_embedding = json.dumps(arr.tolist())

    def __str__(self):
        return f"{self.username} (Level {self.level})"


# ─────────────────────────────────────────────────────────────
# EXERCISE CONTENT
# ─────────────────────────────────────────────────────────────
class ExerciseCategory(models.Model):
    CATEGORY_TYPES = [
        ('alphabet',  'Alphabet'),
        ('phoneme',   'Phonème Groups'),
        ('word',      'Words'),
        ('sentence',  'Sentences'),
        ('quiz',      'Quiz'),
        ('dictee',    'Dictée'),
    ]
    name          = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    order         = models.IntegerField(default=0)
    icon          = models.CharField(max_length=10, default='🔤')
    description   = models.TextField(blank=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Exercise Categories'

    def __str__(self):
        return f"{self.icon} {self.name}"


class Exercise(models.Model):
    category      = models.ForeignKey(ExerciseCategory, on_delete=models.CASCADE,
                                      related_name='exercises')
    order         = models.IntegerField(default=0)
    french_text   = models.CharField(max_length=500)
    ipa           = models.CharField(max_length=200, blank=True)
    english_text  = models.CharField(max_length=500, blank=True)
    hebrew_text   = models.CharField(max_length=500, blank=True)
    example       = models.CharField(max_length=200, blank=True)
    difficulty    = models.IntegerField(default=1)
    phoneme_class = models.CharField(max_length=20, blank=True)  # ← for PhonemeNet v4
    phoneme_groups = models.JSONField(default=list, blank=True)
    audio_file    = models.FileField(upload_to='exercises/audio/', blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.french_text} ({self.ipa})"


# ─────────────────────────────────────────────────────────────
# USER PROGRESS
# ─────────────────────────────────────────────────────────────
class UserProgress(models.Model):
    user            = models.ForeignKey(User, on_delete=models.CASCADE,
                                        related_name='progress')
    exercise        = models.ForeignKey(Exercise, on_delete=models.CASCADE,
                                        related_name='user_progress')
    attempts        = models.IntegerField(default=0)
    best_score      = models.IntegerField(default=0)
    last_score      = models.IntegerField(default=0)
    mastered        = models.BooleanField(default=False)
    mastered_at     = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'exercise')

    def __str__(self):
        return f"{self.user.username} — {self.exercise.french_text}: {self.best_score}%"


class PronunciationAttempt(models.Model):
    user               = models.ForeignKey(User, on_delete=models.CASCADE,
                                           related_name='attempts')
    exercise           = models.ForeignKey(Exercise, on_delete=models.CASCADE,
                                           related_name='attempts')
    overall_score      = models.IntegerField()
    passed             = models.BooleanField()
    phoneme_scores     = models.JSONField(default=list)
    audio_file         = models.FileField(upload_to='attempts/audio/',
                                          blank=True, null=True)
    spectrogram_file   = models.FileField(upload_to='attempts/spectrograms/',
                                          blank=True, null=True)
    model_confidence   = models.FloatField(default=0.0)
    user_feedback      = models.CharField(
        max_length=20,
        choices=[('agree','Agree'),('too_strict','Too strict'),('too_easy','Too easy')],
        blank=True
    )
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.exercise.french_text}: {self.overall_score}%"


# ─────────────────────────────────────────────────────────────
# PHONEME GROUPS
# ─────────────────────────────────────────────────────────────
class PhonemeGroup(models.Model):
    name        = models.CharField(max_length=20)
    ipa         = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    examples    = models.CharField(max_length=200)
    difficulty  = models.IntegerField(default=1)
    order       = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} {self.ipa}"


class UserPhonemeScore(models.Model):
    user          = models.ForeignKey(User, on_delete=models.CASCADE,
                                      related_name='phoneme_scores')
    phoneme_group = models.ForeignKey(PhonemeGroup, on_delete=models.CASCADE)
    average_score = models.FloatField(default=0.0)
    attempt_count = models.IntegerField(default=0)
    mastered      = models.BooleanField(default=False)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'phoneme_group')

    def __str__(self):
        return f"{self.user.username} — {self.phoneme_group.name}: {self.average_score:.1f}%"


# ─────────────────────────────────────────────────────────────
# QUIZ & DICTEE RESULTS
# ─────────────────────────────────────────────────────────────
class QuizResult(models.Model):
    user            = models.ForeignKey(User, on_delete=models.CASCADE,
                                        related_name='quiz_results')
    source_language = models.CharField(max_length=5,
                                       choices=[('en','English'),('he','Hebrew')])
    exercise        = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    spoken_text     = models.CharField(max_length=500, blank=True)
    correct         = models.BooleanField()
    score           = models.IntegerField()
    created_at      = models.DateTimeField(auto_now_add=True)


class DicteeResult(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='dictee_results')
    exercise   = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    typed_text = models.CharField(max_length=500)
    correct    = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)


# ─────────────────────────────────────────────────────────────
# STUDENT ATTEMPTS — PhonemeNet v4 scoring
# ─────────────────────────────────────────────────────────────
class StudentAttempt(models.Model):
    """One pronunciation attempt scored by PhonemeNet v4."""
    student      = models.ForeignKey(User,     on_delete=models.CASCADE)
    exercise     = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    score        = models.IntegerField()
    predicted    = models.CharField(max_length=20)
    correct      = models.BooleanField()
    attempted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} — {self.exercise.french_text} — {self.score}%"

    class Meta:
        ordering = ['-attempted_at']