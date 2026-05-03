"""
core/management/commands/populate_french_content.py
─────────────────────────────────────────────────────────────
Loads ALL French learning content into the database.

RUN WITH:
    python manage.py populate_french_content

LOADS:
    1. Alphabet      — 26 letters with IPA + examples
    2. Phonèmes      — 14 French-specific sound groups
    3. Mots          — 100 words in 5 categories
    4. Phrases       — 20 complete sentences
    5. Quiz          — 30 EN/HE → FR items
    6. Dictée        — 20 listening exercises
─────────────────────────────────────────────────────────────
"""
from django.core.management.base import BaseCommand
from core.models import ExerciseCategory, Exercise, PhonemeGroup


class Command(BaseCommand):
    help = 'Populate the database with all French learning content'

    def handle(self, *args, **kwargs):
        self.stdout.write('\n🇫🇷 Loading French content into database...\n')

        self.load_phoneme_groups()
        self.load_alphabet()
        self.load_phonemes()
        self.load_words()
        self.load_sentences()
        self.load_quiz()
        self.load_dictee()

        self.stdout.write(self.style.SUCCESS('\n✅ All content loaded successfully!\n'))

    # ─────────────────────────────────────────────────────────
    # PHONEME GROUPS (standalone reference table)
    # ─────────────────────────────────────────────────────────
    def load_phoneme_groups(self):
        self.stdout.write('  Loading phoneme groups...')
        groups = [
            ('en/an', '/ɑ̃/', 'enfant, vent, blanc, temps', 'The nasal A — does not exist in English', 1),
            ('on',    '/ɔ̃/', 'bonjour, nom, ton, fond',    'The nasal O — very French!',               1),
            ('un/in', '/œ̃/ /ɛ̃/', 'un, vin, pain, fin',   'Nasal vowels — like English but through nose', 2),
            ('oin',   '/wɛ̃/', 'loin, coin, besoin, soin',  'Combination nasal — unique to French',      3),
            ('ou',    '/u/',   'rouge, tout, vous, bouche', 'Pure U sound — different from English "ou"',1),
            ('eu/œu', '/ø/ /œ/', 'feu, peur, cœur, bleu', 'No equivalent in English or Hebrew',        2),
            ('oi',    '/wa/', 'moi, trois, boire, voir',   'Like "wa" in "water"',                      1),
            ('ui',    '/ɥi/', 'nuit, lui, bruit, cuire',   'Unique French glide — very tricky!',        3),
            ('ch',    '/ʃ/',  'chat, chose, chien, chambre','Like "sh" in English',                     1),
            ('gn',    '/ɲ/',  'agneau, ligne, montagne',    'Like Spanish "ñ" or Italian "gn"',         2),
            ('r',     '/ʁ/',  'rue, rouge, Paris, merci',   'Uvular R — from the back of the throat',   2),
            ('é/è',   '/e/ /ɛ/', 'été, fête, père, mère', 'Two different E sounds in French',          1),
            ('an/am', '/ɑ̃/', 'jambe, lampe, champ, grand', 'AM/AN before consonant = nasal vowel',     2),
            ('ill',   '/j/',  'famille, fille, bille',      'Like "y" in "yes"',                        2),
        ]
        PhonemeGroup.objects.all().delete()
        for i, (name, ipa, examples, desc, diff) in enumerate(groups):
            PhonemeGroup.objects.create(
                name=name, ipa=ipa, examples=examples,
                description=desc, difficulty=diff, order=i
            )
        self.stdout.write(f'    ✓ {len(groups)} phoneme groups')

    # ─────────────────────────────────────────────────────────
    # 1. ALPHABET
    # ─────────────────────────────────────────────────────────
    def load_alphabet(self):
        self.stdout.write('  Loading alphabet...')
        cat, _ = ExerciseCategory.objects.get_or_create(
            category_type='alphabet',
            defaults={'name': 'Alphabet', 'icon': '🔤', 'order': 1,
                      'description': '26 French letters with authentic pronunciation'}
        )
        Exercise.objects.filter(category=cat).delete()

        letters = [
            ('A', '/a/',        'ami, arbre, avril'),
            ('B', '/be/',       'bonjour, bateau, bleu'),
            ('C', '/se/',       'chat, café, cinq'),
            ('D', '/de/',       'doux, dame, donner'),
            ('E', '/ə/',        'être, école, enfant'),
            ('F', '/ɛf/',       'fleur, forêt, famille'),
            ('G', '/ʒe/',       'genre, garçon, grand'),
            ('H', '/aʃ/',       'heure, homme, hôtel'),
            ('I', '/i/',        'île, ici, image'),
            ('J', '/ʒi/',       'jardin, jour, joie'),
            ('K', '/ka/',       'kilo, képi, kiosque'),
            ('L', '/ɛl/',       'lune, lumière, livre'),
            ('M', '/ɛm/',       'mer, maison, matin'),
            ('N', '/ɛn/',       'nuit, nature, neige'),
            ('O', '/o/',        'oiseau, orange, olive'),
            ('P', '/pe/',       'pain, printemps, père'),
            ('Q', '/ky/',       'quatre, qualité, queue'),
            ('R', '/ɛʁ/',       'rue, rose, rouge'),
            ('S', '/ɛs/',       'soleil, soir, stylo'),
            ('T', '/te/',       'table, temps, tête'),
            ('U', '/y/',        'lune, musique, une'),
            ('V', '/ve/',       'vent, vie, ville'),
            ('W', '/dubləve/',  'wagon, wifi, week-end'),
            ('X', '/iks/',      'xylophone, taxi, luxe'),
            ('Y', '/iɡʁɛk/',   'yeux, yaourt, yoga'),
            ('Z', '/zɛd/',      'zéro, zoo, zone'),
        ]
        for i, (letter, ipa, example) in enumerate(letters):
            Exercise.objects.create(
                category=cat, order=i,
                french_text=letter, ipa=ipa,
                english_text=letter, example=example,
                difficulty=1
            )
        self.stdout.write(f'    ✓ {len(letters)} letters')

    # ─────────────────────────────────────────────────────────
    # 2. PHONÈMES
    # ─────────────────────────────────────────────────────────
    def load_phonemes(self):
        self.stdout.write('  Loading phoneme exercises...')
        cat, _ = ExerciseCategory.objects.get_or_create(
            category_type='phoneme',
            defaults={'name': 'Phonèmes', 'icon': '🔊', 'order': 2,
                      'description': 'French-specific sound groups'}
        )
        Exercise.objects.filter(category=cat).delete()

        phonemes = [
            # (french, ipa, english, hebrew, example, difficulty)
            ('en',      '/ɑ̃/',    'nasal a',      'אן בצרפתית',   'enfant, vent',   1),
            ('an',      '/ɑ̃/',    'nasal a',      'אן בצרפתית',   'blanc, grand',   1),
            ('on',      '/ɔ̃/',    'nasal o',      'און בצרפתית',  'bonjour, nom',   1),
            ('un',      '/œ̃/',    'nasal u',      'אן סגור',       'un, lundi',      2),
            ('in',      '/ɛ̃/',    'nasal i',      'אין בצרפתית',  'vin, pain',      2),
            ('ain',     '/ɛ̃/',    'nasal i',      'אין בצרפתית',  'main, pain',     2),
            ('oin',     '/wɛ̃/',   'nasal oi',     'אואין',         'loin, coin',     3),
            ('ou',      '/u/',     'oo sound',     'או צרפתי',      'rouge, vous',    1),
            ('eu',      '/ø/',     'no equivalent','אין מקבילה',   'feu, bleu',      2),
            ('œu',      '/œ/',     'no equivalent','אין מקבילה',   'cœur, peur',     2),
            ('oi',      '/wa/',    'wa sound',     'ואה',           'moi, trois',     1),
            ('ui',      '/ɥi/',    'unique glide', 'ייחודי',        'nuit, lui',      3),
            ('ch',      '/ʃ/',     'sh sound',     'שׁ',            'chat, chose',    1),
            ('gn',      '/ɲ/',     'ny sound',     'ני',            'agneau, ligne',  2),
        ]
        for i, (french, ipa, english, hebrew, example, diff) in enumerate(phonemes):
            Exercise.objects.create(
                category=cat, order=i,
                french_text=french, ipa=ipa,
                english_text=english, hebrew_text=hebrew,
                example=example, difficulty=diff,
                phoneme_groups=[french]
            )
        self.stdout.write(f'    ✓ {len(phonemes)} phoneme exercises')

    # ─────────────────────────────────────────────────────────
    # 3. MOTS (5 categories × 20 words)
    # ─────────────────────────────────────────────────────────
    def load_words(self):
        self.stdout.write('  Loading words...')

        word_categories = {
            'Salutations': {
                'icon': '👋', 'order': 3,
                'words': [
                    ('Bonjour',         '/bɔ̃ʒuʁ/',     'Hello',          'שלום / בוקר טוב'),
                    ('Bonsoir',         '/bɔ̃swaʁ/',    'Good evening',   'ערב טוב'),
                    ('Bonne nuit',      '/bɔn nɥi/',    'Good night',     'לילה טוב'),
                    ('Au revoir',       '/o ʁəvwaʁ/',   'Goodbye',        'להתראות'),
                    ('Salut',           '/saly/',        'Hi / Bye',       'היי / ביי'),
                    ('Merci',           '/mɛʁsi/',       'Thank you',      'תודה'),
                    ("S'il vous plaît", '/sil vu plɛ/', 'Please',         'בבקשה'),
                    ('Excusez-moi',     '/ɛkskuze mwa/','Excuse me',      'סליחה'),
                    ('Pardon',          '/paʁdɔ̃/',      'Sorry',          'סליחה'),
                    ("Je m'appelle",    '/ʒə mapɛl/',   'My name is',     'שמי'),
                    ('Comment allez-vous?', '/kɔmɑ̃ ale vu/', 'How are you?', 'מה שלומך?'),
                    ('Très bien',       '/tʁɛ bjɛ̃/',   'Very well',      'מאוד טוב'),
                    ('Oui',             '/wi/',          'Yes',            'כן'),
                    ('Non',             '/nɔ̃/',          'No',             'לא'),
                    ("S'il te plaît",   '/sil tə plɛ/', 'Please (informal)','בבקשה (לא פורמלי)'),
                    ('De rien',         '/də ʁjɛ̃/',    "You're welcome", 'בשמחה'),
                    ('Bienvenue',       '/bjɛ̃vəny/',    'Welcome',        'ברוך הבא'),
                    ('Enchanté',        '/ɑ̃ʃɑ̃te/',     'Nice to meet you','נעים להכיר'),
                    ('Bonne journée',   '/bɔn ʒuʁne/',  'Have a nice day','יום טוב'),
                    ('À bientôt',       '/a bjɛ̃to/',   'See you soon',   'להתראות בקרוב'),
                ]
            },
            'Chiffres': {
                'icon': '🔢', 'order': 4,
                'words': [
                    ('Un',      '/œ̃/',    'One',    'אחד'),
                    ('Deux',    '/dø/',    'Two',    'שתיים'),
                    ('Trois',   '/tʁwa/',  'Three',  'שלוש'),
                    ('Quatre',  '/katʁ/',  'Four',   'ארבע'),
                    ('Cinq',    '/sɛ̃k/',  'Five',   'חמש'),
                    ('Six',     '/sis/',   'Six',    'שש'),
                    ('Sept',    '/sɛt/',   'Seven',  'שבע'),
                    ('Huit',    '/ɥit/',   'Eight',  'שמונה'),
                    ('Neuf',    '/nœf/',   'Nine',   'תשע'),
                    ('Dix',     '/dis/',   'Ten',    'עשר'),
                    ('Onze',    '/ɔ̃z/',   'Eleven', 'אחד עשר'),
                    ('Douze',   '/duz/',   'Twelve', 'שנים עשר'),
                    ('Vingt',   '/vɛ̃/',   'Twenty', 'עשרים'),
                    ('Trente',  '/tʁɑ̃t/', 'Thirty', 'שלושים'),
                    ('Quarante','/kaʁɑ̃t/','Forty',  'ארבעים'),
                    ('Cinquante','/sɛ̃kɑ̃t/','Fifty', 'חמישים'),
                    ('Cent',    '/sɑ̃/',   'Hundred','מאה'),
                    ('Mille',   '/mil/',   'Thousand','אלף'),
                    ('Premier', '/pʁəmje/','First',  'ראשון'),
                    ('Dernier', '/dɛʁnje/','Last',   'אחרון'),
                ]
            },
            'Couleurs': {
                'icon': '🎨', 'order': 5,
                'words': [
                    ('Rouge',   '/ʁuʒ/',   'Red',    'אדום'),
                    ('Bleu',    '/blø/',    'Blue',   'כחול'),
                    ('Vert',    '/vɛʁ/',    'Green',  'ירוק'),
                    ('Jaune',   '/ʒon/',    'Yellow', 'צהוב'),
                    ('Blanc',   '/blɑ̃/',   'White',  'לבן'),
                    ('Noir',    '/nwaʁ/',   'Black',  'שחור'),
                    ('Orange',  '/ɔʁɑ̃ʒ/', 'Orange', 'כתום'),
                    ('Violet',  '/vjɔlɛ/',  'Purple', 'סגול'),
                    ('Rose',    '/ʁoz/',    'Pink',   'ורוד'),
                    ('Gris',    '/ɡʁi/',    'Grey',   'אפור'),
                    ('Marron',  '/maʁɔ̃/',  'Brown',  'חום'),
                    ('Beige',   '/bɛʒ/',    'Beige',  'בז\''),
                    ('Doré',    '/dɔʁe/',   'Golden', 'זהוב'),
                    ('Argenté', '/aʁʒɑ̃te/','Silver', 'כסוף'),
                    ('Turquoise','/tyʁkwaz/','Turquoise','טורקיז'),
                    ('Bordeaux','/bɔʁdo/',  'Burgundy','בורדו'),
                    ('Clair',   '/klɛʁ/',   'Light',  'בהיר'),
                    ('Foncé',   '/fɔ̃se/',   'Dark',   'כהה'),
                    ('Vif',     '/vif/',     'Bright', 'עז'),
                    ('Pâle',    '/pɑl/',     'Pale',   'חיוור'),
                ]
            },
            'Nourriture': {
                'icon': '🥐', 'order': 6,
                'words': [
                    ('Pain',        '/pɛ̃/',      'Bread',      'לחם'),
                    ('Fromage',     '/fʁɔmaʒ/',   'Cheese',     'גבינה'),
                    ('Vin',         '/vɛ̃/',       'Wine',       'יין'),
                    ('Eau',         '/o/',         'Water',      'מים'),
                    ('Lait',        '/lɛ/',        'Milk',       'חלב'),
                    ('Café',        '/kafe/',      'Coffee',     'קפה'),
                    ('Thé',         '/te/',        'Tea',        'תה'),
                    ('Croissant',   '/kʁwasɑ̃/',  'Croissant',  'קרואסון'),
                    ('Baguette',    '/baɡɛt/',     'Baguette',   'באגט'),
                    ('Beurre',      '/bœʁ/',       'Butter',     'חמאה'),
                    ('Pomme',       '/pɔm/',       'Apple',      'תפוח'),
                    ('Orange',      '/ɔʁɑ̃ʒ/',    'Orange',     'תפוז'),
                    ('Poulet',      '/pulɛ/',      'Chicken',    'עוף'),
                    ('Poisson',     '/pwasɔ̃/',    'Fish',       'דג'),
                    ('Légumes',     '/leɡym/',     'Vegetables', 'ירקות'),
                    ('Soupe',       '/sup/',        'Soup',       'מרק'),
                    ('Gâteau',      '/ɡɑto/',      'Cake',       'עוגה'),
                    ('Chocolat',    '/ʃɔkɔla/',    'Chocolate',  'שוקולד'),
                    ('Sucre',       '/sykʁ/',       'Sugar',      'סוכר'),
                    ('Sel',         '/sɛl/',        'Salt',       'מלח'),
                ]
            },
            'Animaux': {
                'icon': '🐾', 'order': 7,
                'words': [
                    ('Chat',        '/ʃa/',         'Cat',        'חתול'),
                    ('Chien',       '/ʃjɛ̃/',       'Dog',        'כלב'),
                    ('Oiseau',      '/wazo/',        'Bird',       'ציפור'),
                    ('Cheval',      '/ʃəval/',       'Horse',      'סוס'),
                    ('Vache',       '/vaʃ/',         'Cow',        'פרה'),
                    ('Mouton',      '/mutɔ̃/',       'Sheep',      'כבש'),
                    ('Cochon',      '/kɔʃɔ̃/',      'Pig',        'חזיר'),
                    ('Lapin',       '/lapɛ̃/',       'Rabbit',     'ארנב'),
                    ('Lion',        '/ljɔ̃/',        'Lion',       'אריה'),
                    ('Tigre',       '/tiɡʁ/',        'Tiger',      'נמר'),
                    ('Éléphant',    '/elefɑ̃/',      'Elephant',   'פיל'),
                    ('Girafe',      '/ʒiʁaf/',       'Giraffe',    'ג\'ירף'),
                    ('Singe',       '/sɛ̃ʒ/',        'Monkey',     'קוף'),
                    ('Serpent',     '/sɛʁpɑ̃/',      'Snake',      'נחש'),
                    ('Grenouille',  '/ɡʁənuj/',      'Frog',       'צפרדע'),
                    ('Papillon',    '/papijɔ̃/',     'Butterfly',  'פרפר'),
                    ('Abeille',     '/abɛj/',        'Bee',        'דבורה'),
                    ('Poisson',     '/pwasɔ̃/',      'Fish',       'דג'),
                    ('Tortue',      '/tɔʁty/',       'Turtle',     'צב'),
                    ('Renard',      '/ʁənaʁ/',       'Fox',        'שועל'),
                ]
            },
        }

        total = 0
        for cat_name, data in word_categories.items():
            cat, _ = ExerciseCategory.objects.get_or_create(
                name=cat_name,
                category_type='word',
                defaults={'icon': data['icon'], 'order': data['order'],
                          'description': f'French {cat_name.lower()} vocabulary'}
            )
            Exercise.objects.filter(category=cat).delete()
            for i, (french, ipa, english, hebrew) in enumerate(data['words']):
                Exercise.objects.create(
                    category=cat, order=i,
                    french_text=french, ipa=ipa,
                    english_text=english, hebrew_text=hebrew,
                    difficulty=1
                )
                total += 1
        self.stdout.write(f'    ✓ {total} words in {len(word_categories)} categories')

    # ─────────────────────────────────────────────────────────
    # 4. PHRASES (sentences)
    # ─────────────────────────────────────────────────────────
    def load_sentences(self):
        self.stdout.write('  Loading sentences...')
        cat, _ = ExerciseCategory.objects.get_or_create(
            category_type='sentence',
            defaults={'name': 'Phrases', 'icon': '💬', 'order': 8,
                      'description': 'Complete French sentences'}
        )
        Exercise.objects.filter(category=cat).delete()

        sentences = [
            ("Comment vous appelez-vous ?",
             "/kɔmɑ̃ vu zapəle vu/",
             "What is your name?",
             "?מה שמך",  1),

            ("Je m'appelle Marie.",
             "/ʒə mapɛl maʁi/",
             "My name is Marie.",
             ".שמי מארי",  1),

            ("Où est la gare, s'il vous plaît ?",
             "/u ɛ la ɡaʁ sil vu plɛ/",
             "Where is the train station, please?",
             "?איפה תחנת הרכבת, בבקשה",  2),

            ("Je voudrais un café, s'il vous plaît.",
             "/ʒə vudʁɛ œ̃ kafe sil vu plɛ/",
             "I would like a coffee, please.",
             ".אני רוצה קפה, בבקשה",  2),

            ("Quel temps fait-il aujourd'hui ?",
             "/kɛl tɑ̃ fɛ til oʒuʁdɥi/",
             "What is the weather like today?",
             "?מה מזג האוויר היום",  2),

            ("Il fait beau aujourd'hui.",
             "/il fɛ bo oʒuʁdɥi/",
             "The weather is nice today.",
             ".מזג האוויר יפה היום",  1),

            ("J'aime apprendre le français.",
             "/ʒɛm apʁɑ̃dʁ lə fʁɑ̃sɛ/",
             "I love learning French.",
             ".אני אוהב ללמוד צרפתית",  1),

            ("Pouvez-vous parler plus lentement ?",
             "/puve vu paʁle ply lɑ̃tmɑ̃/",
             "Can you speak more slowly?",
             "?יכולתם לדבר יותר לאט",  3),

            ("Je ne comprends pas.",
             "/ʒə nə kɔ̃pʁɑ̃ pa/",
             "I don't understand.",
             ".אני לא מבין",  2),

            ("Répétez, s'il vous plaît.",
             "/ʁepete sil vu plɛ/",
             "Please repeat.",
             ".חזרו, בבקשה",  1),

            ("Combien ça coûte ?",
             "/kɔ̃bjɛ̃ sa kut/",
             "How much does it cost?",
             "?כמה זה עולה",  2),

            ("À quelle heure part le train ?",
             "/a kɛl œʁ paʁ lə tʁɛ̃/",
             "What time does the train leave?",
             "?באיזו שעה יוצא הרכבת",  3),

            ("Je suis étudiant.",
             "/ʒə sɥi etydjɑ̃/",
             "I am a student.",
             ".אני סטודנט",  1),

            ("Paris est une belle ville.",
             "/paʁi ɛ yn bɛl vil/",
             "Paris is a beautiful city.",
             ".פריז היא עיר יפה",  1),

            ("J'habite à Jérusalem.",
             "/ʒabit a ʒeʁyzalɛm/",
             "I live in Jerusalem.",
             ".אני גר בירושלים",  1),

            ("Quelle est votre profession ?",
             "/kɛl ɛ vɔtʁ pʁɔfɛsjɔ̃/",
             "What is your profession?",
             "?מה המקצוע שלך",  2),

            ("Je parle un peu français.",
             "/ʒə paʁl œ̃ pø fʁɑ̃sɛ/",
             "I speak a little French.",
             ".אני מדבר קצת צרפתית",  2),

            ("Avez-vous une chambre libre ?",
             "/ave vu yn ʃɑ̃bʁ libʁ/",
             "Do you have a free room?",
             "?יש לכם חדר פנוי",  3),

            ("L'addition, s'il vous plaît.",
             "/ladisjɔ̃ sil vu plɛ/",
             "The bill, please.",
             ".החשבון, בבקשה",  2),

            ("Bonne chance et bonne continuation !",
             "/bɔn ʃɑ̃s e bɔn kɔ̃tinɥasjɔ̃/",
             "Good luck and keep it up!",
             "!בהצלחה והמשך טוב",  3),
        ]
        for i, (french, ipa, english, hebrew, diff) in enumerate(sentences):
            Exercise.objects.create(
                category=cat, order=i,
                french_text=french, ipa=ipa,
                english_text=english, hebrew_text=hebrew,
                difficulty=diff
            )
        self.stdout.write(f'    ✓ {len(sentences)} sentences')

    # ─────────────────────────────────────────────────────────
    # 5. QUIZ (EN/HE → FR)
    # ─────────────────────────────────────────────────────────
    def load_quiz(self):
        self.stdout.write('  Loading quiz items...')
        cat, _ = ExerciseCategory.objects.get_or_create(
            category_type='quiz',
            defaults={'name': 'Quiz', 'icon': '🧠', 'order': 9,
                      'description': 'Translate and pronounce in French'}
        )
        Exercise.objects.filter(category=cat).delete()

        items = [
            # (french, ipa, english, hebrew, difficulty)
            ('Chat',        '/ʃa/',         'Cat',          'חתול',     1),
            ('Chien',       '/ʃjɛ̃/',       'Dog',          'כלב',      1),
            ('Eau',         '/o/',           'Water',        'מים',      1),
            ('Pain',        '/pɛ̃/',         'Bread',        'לחם',      1),
            ('Bonjour',     '/bɔ̃ʒuʁ/',     'Hello',        'שלום',     1),
            ('Merci',       '/mɛʁsi/',       'Thank you',    'תודה',     1),
            ('Oui',         '/wi/',           'Yes',          'כן',       1),
            ('Non',         '/nɔ̃/',          'No',           'לא',       1),
            ('Maison',      '/mɛzɔ̃/',       'House',        'בית',      1),
            ('Livre',       '/livʁ/',         'Book',         'ספר',      1),
            ('Rouge',       '/ʁuʒ/',          'Red',          'אדום',     1),
            ('Bleu',        '/blø/',          'Blue',         'כחול',     1),
            ('Soleil',      '/sɔlɛj/',        'Sun',          'שמש',      2),
            ('Lune',        '/lyn/',           'Moon',         'ירח',      2),
            ('Nuit',        '/nɥi/',          'Night',        'לילה',     2),
            ('Jour',        '/ʒuʁ/',          'Day',          'יום',      1),
            ('Père',        '/pɛʁ/',          'Father',       'אבא',      1),
            ('Mère',        '/mɛʁ/',          'Mother',       'אמא',      1),
            ('Frère',       '/fʁɛʁ/',         'Brother',      'אח',       2),
            ('Sœur',        '/sœʁ/',          'Sister',       'אחות',     2),
            ('Amour',       '/amuʁ/',         'Love',         'אהבה',     2),
            ('Liberté',     '/libɛʁte/',      'Freedom',      'חירות',    2),
            ('Bonheur',     '/bɔnœʁ/',        'Happiness',    'אושר',     2),
            ('Chanson',     '/ʃɑ̃sɔ̃/',       'Song',         'שיר',      2),
            ('Musique',     '/myzik/',         'Music',        'מוזיקה',   2),
            ('École',       '/ekɔl/',          'School',       'בית ספר',  2),
            ('Professeur',  '/pʁɔfɛsœʁ/',    'Teacher',      'מורה',     3),
            ('Étudiant',    '/etydjɑ̃/',      'Student',      'סטודנט',   2),
            ('Fenêtre',     '/fənɛtʁ/',       'Window',       'חלון',     3),
            ('Ordinateur',  '/ɔʁdinatœʁ/',   'Computer',     'מחשב',     3),
        ]
        for i, (french, ipa, english, hebrew, diff) in enumerate(items):
            Exercise.objects.create(
                category=cat, order=i,
                french_text=french, ipa=ipa,
                english_text=english, hebrew_text=hebrew,
                difficulty=diff
            )
        self.stdout.write(f'    ✓ {len(items)} quiz items')

    # ─────────────────────────────────────────────────────────
    # 6. DICTÉE (listening exercises)
    # ─────────────────────────────────────────────────────────
    def load_dictee(self):
        self.stdout.write('  Loading dictée exercises...')
        cat, _ = ExerciseCategory.objects.get_or_create(
            category_type='dictee',
            defaults={'name': 'Dictée', 'icon': '👂', 'order': 10,
                      'description': 'Listen and write what you hear'}
        )
        Exercise.objects.filter(category=cat).delete()

        items = [
            # Level 1 — single words
            ('chat',        '/ʃa/',         'cat',          'חתול',     1),
            ('pain',        '/pɛ̃/',         'bread',        'לחם',      1),
            ('eau',         '/o/',           'water',        'מים',      1),
            ('rouge',       '/ʁuʒ/',         'red',          'אדום',     1),
            ('bonjour',     '/bɔ̃ʒuʁ/',     'hello',        'שלום',     1),
            ('merci',       '/mɛʁsi/',       'thank you',    'תודה',     1),
            ('nuit',        '/nɥi/',         'night',        'לילה',     1),
            ('trois',       '/tʁwa/',        'three',        'שלוש',     1),
            ('maison',      '/mɛzɔ̃/',       'house',        'בית',      2),
            ('croissant',   '/kʁwasɑ̃/',    'croissant',    'קרואסון',  2),
            # Level 2 — short phrases
            ('au revoir',       '/o ʁəvwaʁ/',    'goodbye',          'להתראות',  2),
            ('bonne nuit',      '/bɔn nɥi/',     'good night',       'לילה טוב', 2),
            ('s\'il vous plaît','/sil vu plɛ/',  'please',           'בבקשה',    2),
            ('je comprends',    '/ʒə kɔ̃pʁɑ̃/',  'I understand',     'אני מבין', 2),
            ('c\'est bon',      '/sɛ bɔ̃/',      'it\'s good',       'זה טוב',   2),
            # Level 3 — longer phrases
            ('je ne sais pas',      '/ʒə nə sɛ pa/',    'I don\'t know',    'אני לא יודע',   3),
            ('bonne journée',       '/bɔn ʒuʁne/',      'have a nice day',  'יום טוב',       2),
            ('enchanté de vous voir','/ɑ̃ʃɑ̃te/',       'nice to see you',  'נעים לראותך',   3),
            ('quelle heure est-il', '/kɛl œʁ ɛ til/',   'what time is it',  '?כמה השעה',     3),
            ('je parle français',   '/ʒə paʁl fʁɑ̃sɛ/', 'I speak French',   'אני מדבר צרפתית',3),
        ]
        for i, (french, ipa, english, hebrew, diff) in enumerate(items):
            Exercise.objects.create(
                category=cat, order=i,
                french_text=french, ipa=ipa,
                english_text=english, hebrew_text=hebrew,
                difficulty=diff
            )
        self.stdout.write(f'    ✓ {len(items)} dictée exercises')
