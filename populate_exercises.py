import os, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parle_francais.settings')
django.setup()

from core.models import Exercise

exercises = [
    # (french_word,      phoneme_class,   english,          difficulty)
    ('bonjour',         'nasal',      'hello',              1),
    ('maison',           'nasal',      'house',              1),
    ('manger',           'nasal',      'to eat',             1),
    ('enfant',           'nasal',      'child',              1),
    ('montagne',         'nasal',      'mountain',           2),
    ('chat',             'fricative',  'cat',                1),
    ('chose',            'fricative',  'thing',              1),
    ('rouge',            'fricative',  'red',                1),
    ('chercher',         'fricative',  'to look for',       2),
    ('feu',              'eu_sound',   'fire',               1),
    ('bleu',             'eu_sound',   'blue',               1),
    ('fleur',            'eu_sound',   'flower',             1),
    ('heureux',          'eu_sound',   'happy',              2),
    ('moi',              'oi_ui',      'me',                 1),
    ('nuit',             'oi_ui',      'night',              1),
    ('voir',             'oi_ui',      'to see',             1),
    ('bruit',            'oi_ui',      'noise',              1),
    ('lune',             'liquid_l',   'moon',               1),
    ('soleil',           'liquid_l',   'sun',                1),
    ('famille',          'liquid_l',   'family',             1),
    ('belle',            'liquid_l',   'beautiful',          1),
    ('merci',            'standard',   'thank you',          1),
    ('école',            'standard',   'school',             1),
    ('voiture',          'standard',   'car',                1),
    ('boulangerie',      'standard',   'bakery',             2),
]

created = 0
for french, cls, english, diff in exercises:
    obj, new = Exercise.objects.get_or_create(
        french_text = french,
        defaults    = {
            'phoneme_class': cls,
            'english_trans': english,
            'difficulty':    diff,
        }
    )
    if new:
        created += 1
        print(f"  ✅ {french:20s}  [{cls}]")

print(f"\n✅ Done! Created {created} new exercises.")
print(f"   Total in database: {Exercise.objects.count()}")