from django.contrib import admin
from .models import (
    User, Exercise, ExerciseCategory, UserProgress,
    PronunciationAttempt, PhonemeGroup, UserPhonemeScore,
    QuizResult, DicteeResult, StudentAttempt
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display  = ['username', 'level', 'xp', 'streak_days', 'native_language']
    list_filter   = ['native_language', 'level']
    search_fields = ['username', 'email']


@admin.register(ExerciseCategory)
class ExerciseCategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category_type', 'order', 'icon']
    list_filter   = ['category_type']


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display  = ['french_text', 'phoneme_class', 'english_text', 'difficulty']
    list_filter   = ['phoneme_class', 'difficulty', 'category']
    search_fields = ['french_text', 'english_text', 'ipa']


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display  = ['user', 'exercise', 'best_score', 'mastered', 'attempts']
    list_filter   = ['mastered']


@admin.register(PronunciationAttempt)
class PronunciationAttemptAdmin(admin.ModelAdmin):
    list_display    = ['user', 'exercise', 'overall_score', 'passed', 'created_at']
    list_filter     = ['passed']
    readonly_fields = ['created_at']


@admin.register(PhonemeGroup)
class PhonemeGroupAdmin(admin.ModelAdmin):
    list_display  = ['name', 'ipa', 'difficulty', 'order']
    ordering      = ['order']


@admin.register(StudentAttempt)
class StudentAttemptAdmin(admin.ModelAdmin):
    list_display    = ['student', 'exercise', 'score', 'correct', 'attempted_at']
    list_filter     = ['correct', 'exercise__phoneme_class']
    readonly_fields = ['attempted_at']