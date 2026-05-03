/**
 * core/static/core/js/app.js
 * ─────────────────────────────────────────────────────────────
 * Shared JavaScript for all Parle Français pages.
 *
 * Key features:
 *   - MicRecorder: records audio, sends to Django API
 *   - showScore(): displays CNN model results
 *   - VoiceAuth: handles voice login/register
 *   - Toast notifications
 *   - TTS (Text-to-Speech) with French voice
 * ─────────────────────────────────────────────────────────────
 */

'use strict';

// ─────────────────────────────────────────────────────────────
// TTS — Text-to-Speech (French)
// ─────────────────────────────────────────────────────────────
const TTS = {
  speak(text, rate = 1.0) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'fr-FR';
    utterance.rate = rate;
    utterance.pitch = 1.0;

    // Try to use a French voice
    const voices = window.speechSynthesis.getVoices();
    const frVoice = voices.find(v => v.lang.startsWith('fr'));
    if (frVoice) utterance.voice = frVoice;

    window.speechSynthesis.speak(utterance);
  },

  slow(text) { this.speak(text, 0.65); },
};

// Load voices on page load (some browsers need this trigger)
if (window.speechSynthesis) {
  window.speechSynthesis.getVoices();
  window.speechSynthesis.addEventListener('voiceschanged', () => {});
}


// ─────────────────────────────────────────────────────────────
// MIC RECORDER
// ─────────────────────────────────────────────────────────────
class MicRecorder {
  /**
   * Manages microphone recording and sends audio to Django API.
   *
   * Usage:
   *   const mic = new MicRecorder({
   *     exerciseId: 42,
   *     onScore: (result) => { showScore(result); },
   *     waveformId: 'my-waveform',
   *   });
   *   mic.toggle(); // start/stop recording
   */
  constructor({ exerciseId, onScore, onError, waveformId }) {
    this.exerciseId = exerciseId;
    this.onScore = onScore;
    this.onError = onError || console.error;
    this.waveformId = waveformId;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
    this.waveInterval = null;
  }

  async toggle(btnEl) {
    if (this.isRecording) {
      this.stop(btnEl);
    } else {
      await this.start(btnEl);
    }
  }

  async start(btnEl) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioChunks = [];

      // Try WebM first (Chrome), fall back to OGG (Firefox)
      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/ogg';

      this.mediaRecorder = new MediaRecorder(stream, { mimeType });
      this.mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) this.audioChunks.push(e.data);
      };
      this.mediaRecorder.onstop = () => this._sendToAPI();

      this.mediaRecorder.start(100); // collect data every 100ms
      this.isRecording = true;

      if (btnEl) btnEl.classList.add('recording');
      this._animateWaveform(true);
      showToast('🎤 Recording…', 'info');

    } catch (err) {
      this.onError('Microphone access denied: ' + err.message);
      showToast('Microphone access denied!', 'error');
    }
  }

  stop(btnEl) {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.mediaRecorder.stream.getTracks().forEach(t => t.stop());
      this.isRecording = false;
      if (btnEl) btnEl.classList.remove('recording');
      this._animateWaveform(false);
      showToast('Processing…', 'info');
    }
  }

  async _sendToAPI() {
    const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('exercise_id', this.exerciseId);

    try {
      const response = await fetch(DJANGO_CONTEXT.apiScoreUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN },
        body: formData,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      this.onScore(result);

    } catch (err) {
      this.onError(err.message);
      showToast('Scoring failed. Please try again.', 'error');
    }
  }

  _animateWaveform(active) {
    const container = document.getElementById(this.waveformId);
    if (!container) return;
    clearInterval(this.waveInterval);

    const bars = container.querySelectorAll('.wave-bar');
    bars.forEach(b => b.classList.toggle('active', active));

    if (active) {
      this.waveInterval = setInterval(() => {
        bars.forEach(b => {
          b.style.height = (4 + Math.random() * 32) + 'px';
        });
      }, 80);
    } else {
      clearInterval(this.waveInterval);
      bars.forEach(b => b.style.height = (4 + Math.random() * 8) + 'px');
    }
  }
}


// ─────────────────────────────────────────────────────────────
// SCORE DISPLAY
// ─────────────────────────────────────────────────────────────
function showScore(result, containerId = 'score-display') {
  const el = document.getElementById(containerId);
  if (!el) return;

  el.style.display = 'block';
  el.className = `score-display show ${result.pass ? 'pass' : 'fail'}`;

  const numEl = el.querySelector('.score-number');
  const labelEl = el.querySelector('.score-label');
  const feedbackEl = el.querySelector('.score-feedback');
  const phonemeEl = el.querySelector('.phoneme-breakdown');

  if (numEl) numEl.textContent = result.score;
  if (labelEl) labelEl.textContent = result.feedback;
  if (feedbackEl && result.pass !== undefined) {
    feedbackEl.textContent = result.pass
      ? `✓ Score: ${result.score}% — Passed!`
      : `Score: ${result.score}% — Keep practicing!`;
  }

  // Per-phoneme chips
  if (phonemeEl && result.phonemes && result.phonemes.length > 0) {
    phonemeEl.innerHTML = result.phonemes.map(p =>
      `<span class="phoneme-chip ${p.correct ? 'ok' : 'bad'}" title="${p.score}%">${p.phoneme}</span>`
    ).join('');
  }

  // XP notification
  if (result.xp_gained > 0) {
    setTimeout(() => showToast(`+${result.xp_gained} XP!`, 'success'), 500);
  }

  showToast(
    result.pass ? `✓ ${result.score}% — ${result.feedback}` : `${result.score}% — Réessayez !`,
    result.pass ? 'success' : 'error'
  );
}


// ─────────────────────────────────────────────────────────────
// VOICE AUTHENTICATION
// ─────────────────────────────────────────────────────────────
const VoiceAuth = {
  recorder: null,
  audioChunks: [],

  async record(durationMs = 3000) {
    /**
     * Records audio for voice login/register.
     * Returns a Promise that resolves with the audio Blob.
     */
    return new Promise(async (resolve, reject) => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mimeType = MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm' : 'audio/ogg';

        const mr = new MediaRecorder(stream, { mimeType });
        const chunks = [];
        mr.ondataavailable = e => chunks.push(e.data);
        mr.onstop = () => {
          stream.getTracks().forEach(t => t.stop());
          resolve(new Blob(chunks, { type: mimeType }));
        };
        mr.start(100);
        setTimeout(() => mr.stop(), durationMs);
      } catch (err) {
        reject(err);
      }
    });
  },

  async login(username, passwordWord) {
    showToast(`🎤 Say: "${passwordWord}"`, 'info');

    // Wait 500ms then record
    await new Promise(r => setTimeout(r, 500));
    const audioBlob = await this.record(3000);

    const formData = new FormData();
    formData.append('audio', audioBlob, 'voice_login.webm');
    formData.append('username', username);

    const response = await fetch(DJANGO_CONTEXT.apiVoiceLoginUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
      body: formData,
    });

    const result = await response.json();

    if (result.authenticated) {
      showToast('✓ Voice recognized!', 'success');
      setTimeout(() => window.location.href = result.redirect || '/', 1000);
    } else {
      showToast(result.message || 'Voice not recognized', 'error');
    }

    return result;
  },

  async register(username, email, passwordWord) {
    showToast(`🎤 Say: "${passwordWord}" to set your voice password`, 'info');

    await new Promise(r => setTimeout(r, 800));
    const audioBlob = await this.record(3000);

    const formData = new FormData();
    formData.append('audio', audioBlob, 'voice_register.webm');
    formData.append('username', username);
    formData.append('email', email);
    formData.append('password_word', passwordWord);

    const response = await fetch(DJANGO_CONTEXT.apiVoiceRegisterUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
      body: formData,
    });

    const result = await response.json();

    if (result.success) {
      showToast(`✓ ${result.message}`, 'success');
      setTimeout(() => window.location.href = result.redirect || '/', 1200);
    } else {
      showToast(result.error || 'Registration failed', 'error');
    }

    return result;
  },
};


// ─────────────────────────────────────────────────────────────
// WAVEFORM BUILDER
// ─────────────────────────────────────────────────────────────
function buildWaveform(containerId, barCount = 20) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = Array.from({ length: barCount }, (_, i) =>
    `<div class="wave-bar" style="height:${4 + Math.random() * 8}px"></div>`
  ).join('');
}


// ─────────────────────────────────────────────────────────────
// TOAST NOTIFICATIONS
// ─────────────────────────────────────────────────────────────
let _toastTimer;
function showToast(message, type = 'info') {
  const toast = document.getElementById('toast');
  if (!toast) return;
  clearTimeout(_toastTimer);
  toast.textContent = message;
  toast.className = `toast ${type} show`;
  _toastTimer = setTimeout(() => toast.classList.remove('show'), 3500);
}


// ─────────────────────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Build all waveforms on the page
  document.querySelectorAll('[data-waveform]').forEach(el => {
    buildWaveform(el.id);
  });
});
