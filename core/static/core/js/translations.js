// ════════════════════════════════════════════════════════════════
//  Parle Français — Interface Translations
//  Languages: fr (Français), en (English), he (עברית)
// ════════════════════════════════════════════════════════════════

const TRANSLATIONS = {
  fr: {
    // Navigation
    home: "Accueil",
    alphabet: "Alphabet",
    phonemes: "Phonèmes",
    words: "Mots",
    sentences: "Phrases",
    quiz: "Quiz",
    dictee: "Dictée",
    logout: "Déconnexion",
    // Login page
    login_title: "Se connecter",
    register_title: "S'inscrire",
    username: "Nom d'utilisateur",
    email: "Email",
    voice_password: "Mot de passe vocal",
    voice_instructions: "Cliquez le micro, prononcez votre mot, puis cliquez à nouveau pour arrêter.",
    login_instructions: "Cliquez le micro, prononcez votre mot de passe, puis cliquez à nouveau pour arrêter.",
    press_to_start: "Appuyez pour commencer",
    enter_word_then_press: "Entrez un mot puis appuyez",
    create_account: "Créer mon compte vocal",
    connect: "Se connecter",
    text_password: "Mot de passe texte (optionnel)",
    choose_voice_word: "Votre mot de passe vocal (un mot en français)",
    voice_word_hint: "Choisissez un mot français que vous prononcerez pour vous connecter",
    voice_protected: "Votre voix est chiffrée et protégée.",
    administration: "Administration",
    // Home page
    hello: "Bonjour",
    ai_active: "IA Phonème active",
    days: "jour",
    days_plural: "jours",
    level: "Niv.",
    learning_modules: "Modules d'apprentissage",
    continue_learning: "Continuer à apprendre",
    // Modules
    alphabet_desc: "26 lettres avec prononciation française authentique",
    phonemes_desc: "en, on, un, oi, oin, gn, ch et plus encore",
    words_desc: "Vocabulaire français courant avec score de prononciation",
    sentences_desc: "Répétition de phrases complètes et entraînement à la fluidité",
    quiz_desc: "Entendre en anglais/hébreu → dire en français",
    dictee_desc: "Écouter et taper ce que vous entendez en français",
    not_started: "Pas encore commencé",
    completed: "complétés",
    // Phonemes section
    french_sounds: "Sons spécifiques au français 🇫🇷",
    french_sounds_desc: "Ces sons n'existent pas en anglais ni en hébreu — ce sont les plus importants à maîtriser",
  },

  en: {
    // Navigation
    home: "Home",
    alphabet: "Alphabet",
    phonemes: "Phonemes",
    words: "Words",
    sentences: "Sentences",
    quiz: "Quiz",
    dictee: "Dictation",
    logout: "Logout",
    // Login page
    login_title: "Sign In",
    register_title: "Sign Up",
    username: "Username",
    email: "Email",
    voice_password: "Voice Password",
    voice_instructions: "Click the mic, say your word, then click again to stop.",
    login_instructions: "Click the mic, say your password, then click again to stop.",
    press_to_start: "Press to start",
    enter_word_then_press: "Enter a word then press",
    create_account: "Create my voice account",
    connect: "Sign In",
    text_password: "Text password (optional)",
    choose_voice_word: "Your voice password (a French word)",
    voice_word_hint: "Choose a French word you will say to log in",
    voice_protected: "Your voice is encrypted and protected.",
    administration: "Administration",
    // Home page
    hello: "Hello",
    ai_active: "Phoneme AI active",
    days: "day",
    days_plural: "days",
    level: "Lv.",
    learning_modules: "Learning Modules",
    continue_learning: "Continue Learning",
    // Modules
    alphabet_desc: "26 letters with authentic French pronunciation",
    phonemes_desc: "en, on, un, oi, oin, gn, ch and more",
    words_desc: "Common French vocabulary with pronunciation score",
    sentences_desc: "Full sentence repetition and fluency training",
    quiz_desc: "Hear in English/Hebrew → say in French",
    dictee_desc: "Listen and type what you hear in French",
    not_started: "Not started yet",
    completed: "completed",
    // Phonemes section
    french_sounds: "French-specific sounds 🇫🇷",
    french_sounds_desc: "These sounds don't exist in English or Hebrew — they are the most important to master",
  },

  he: {
    // Navigation
    home: "בית",
    alphabet: "אלפבית",
    phonemes: "פונמות",
    words: "מילים",
    sentences: "משפטים",
    quiz: "חידון",
    dictee: "כתיב",
    logout: "התנתק",
    // Login page
    login_title: "התחברות",
    register_title: "הרשמה",
    username: "שם משתמש",
    email: "אימייל",
    voice_password: "סיסמה קולית",
    voice_instructions: "לחץ על המיקרופון, אמור את המילה, ולחץ שוב לעצירה.",
    login_instructions: "לחץ על המיקרופון, אמור את הסיסמה, ולחץ שוב לעצירה.",
    press_to_start: "לחץ להתחלה",
    enter_word_then_press: "הכנס מילה ולחץ",
    create_account: "צור חשבון קולי",
    connect: "התחבר",
    text_password: "סיסמת טקסט (אופציונלי)",
    choose_voice_word: "סיסמה קולית (מילה בצרפתית)",
    voice_word_hint: "בחר מילה צרפתית שתאמר בכל כניסה",
    voice_protected: "הקול שלך מוצפן ומוגן.",
    administration: "ניהול",
    // Home page
    hello: "שלום",
    ai_active: "בינה מלאכותית פעילה",
    days: "יום",
    days_plural: "ימים",
    level: "רמה",
    learning_modules: "מודולי למידה",
    continue_learning: "המשך ללמוד",
    // Modules
    alphabet_desc: "26 אותיות עם הגייה צרפתית אותנטית",
    phonemes_desc: "en, on, un, oi, oin, gn, ch ועוד",
    words_desc: "אוצר מילים צרפתי נפוץ עם ציון הגייה",
    sentences_desc: "חזרה על משפטים מלאים ואימון שטף",
    quiz_desc: "שמע באנגלית/עברית ← אמור בצרפתית",
    dictee_desc: "הקשב והקלד מה שאתה שומע בצרפתית",
    not_started: "טרם התחיל",
    completed: "הושלמו",
    // Phonemes section
    french_sounds: "צלילים ייחודיים לצרפתית 🇫🇷",
    french_sounds_desc: "צלילים אלה אינם קיימים בעברית או באנגלית — אלה החשובים ביותר לשליטה",
  }
};

// ── Language Manager ──────────────────────────────────────────
const LangManager = {
  current: localStorage.getItem('pf_lang') || 'en',

  set: function(lang) {
    this.current = lang;
    localStorage.setItem('pf_lang', lang);
    this.apply();
    // Update RTL for Hebrew
    document.documentElement.setAttribute('dir', lang === 'he' ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', lang);
  },

  t: function(key) {
    return (TRANSLATIONS[this.current] && TRANSLATIONS[this.current][key])
      ? TRANSLATIONS[this.current][key]
      : (TRANSLATIONS['en'][key] || key);
  },

  apply: function() {
    // Apply translations to all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      el.textContent = this.t(key);
    });
    // Apply placeholder translations
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      el.placeholder = this.t(key);
    });
    // Update active button
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === this.current);
    });
  }
};

// ── Language Switcher Widget HTML ─────────────────────────────
function injectLangSwitcher() {
  const switcher = document.createElement('div');
  switcher.id = 'lang-switcher';
  switcher.innerHTML = `
    <button class="lang-btn ${LangManager.current === 'fr' ? 'active' : ''}" data-lang="fr" onclick="LangManager.set('fr')">🇫🇷</button>
    <button class="lang-btn ${LangManager.current === 'en' ? 'active' : ''}" data-lang="en" onclick="LangManager.set('en')">🇬🇧</button>
    <button class="lang-btn ${LangManager.current === 'he' ? 'active' : ''}" data-lang="he" onclick="LangManager.set('he')">🇮🇱</button>
  `;
  switcher.style.cssText = `
    position: fixed;
    top: 16px;
    right: 16px;
    z-index: 9999;
    display: flex;
    gap: 6px;
    background: var(--card, #1e1e2e);
    border: 1px solid var(--border, #333);
    border-radius: 12px;
    padding: 6px 10px;
  `;
  document.body.appendChild(switcher);
}

// ── CSS for lang buttons ──────────────────────────────────────
const langStyle = document.createElement('style');
langStyle.textContent = `
  .lang-btn {
    background: none;
    border: none;
    font-size: 1.3rem;
    cursor: pointer;
    opacity: 0.4;
    transition: opacity 0.2s, transform 0.2s;
    padding: 2px;
  }
  .lang-btn:hover { opacity: 0.8; transform: scale(1.15); }
  .lang-btn.active { opacity: 1; transform: scale(1.2); }
`;
document.head.appendChild(langStyle);

// ── Initialize on DOM ready ───────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  injectLangSwitcher();
  LangManager.set(LangManager.current);
});