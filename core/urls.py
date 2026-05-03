from django.urls import path
from . import views

# NO app_name namespace — keeps all existing templates working as-is

urlpatterns = [
    # ── Page views (original) ────────────────────────────────
    path('',            views.home,           name='home'),
    path('alphabet/',   views.alphabet_view,  name='alphabet'),
    path('phonemes/',   views.phonemes_view,  name='phonemes'),
    path('words/',      views.words_view,     name='words'),
    path('sentences/',  views.sentences_view, name='sentences'),
    path('quiz/',       views.quiz_view,      name='quiz'),
    path('dictee/',     views.dictee_view,    name='dictee'),
    path('stats/',      views.stats_view,     name='stats'),

    # ── Auth views ───────────────────────────────────────────
    path('login/',      views.login_view,     name='login'),
    path('register/',   views.register_view,  name='register'),
    path('logout/',     views.logout_view,    name='logout'),

    # ── Original API endpoints ───────────────────────────────
    path('api/score/',           views.api_score_pronunciation, name='api_score'),
    path('api/voice/register/',  views.api_voice_register,      name='api_voice_register'),
    path('api/voice/login/',     views.api_voice_login,         name='api_voice_login'),
    path('api/feedback/',        views.api_update_feedback,     name='api_feedback'),
    path('api/dictee/',          views.api_save_dictee,         name='api_dictee'),

    # ── New PhonemeNet v4 endpoints ──────────────────────────
    path('pronunciation/<int:exercise_id>/', views.pronunciation, name='pronunciation'),
    path('score/<int:exercise_id>/',         views.score_attempt, name='score'),
    path('dashboard/',                        views.dashboard,     name='dashboard'),
    path('api/exercises/', views.api_exercises, name='api_exercises'),
    path('api/text-login/', views.api_text_login, name='api_text_login'),
    path('qa/', views.qa_tests, name='qa_tests'),
    path('api/score-letter/', views.api_score_letter, name='api_score_letter'),
]