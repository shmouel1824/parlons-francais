"""
populate_from_audio.py
Reads all files in gtts_audio/ and populates the database automatically.
Run from the project root (where manage.py is):
    python populate_from_audio.py
"""
import os, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parle_francais.settings')
django.setup()

from core.models import Exercise, ExerciseCategory

# ── Phoneme class definitions ────────────────────────────────
PHONEME_CLASSES = {
    'nasal':     {'name': 'Nasales',    'icon': '👃', 'desc': 'Sons nasaux: on, an, in, un'},
    'fricative': {'name': 'Fricatives', 'icon': '💨', 'desc': 'Sons fricatifs: ch, r, j'},
    'eu_sound':  {'name': 'Son EU',     'icon': '🔵', 'desc': 'Son EU/OEU: feu, bleu, coeur'},
    'oi_ui':     {'name': 'OI / UI',    'icon': '🌊', 'desc': 'Sons OI et UI: moi, nuit, oui'},
    'liquid_l':  {'name': 'L liquide',  'icon': '💧', 'desc': 'Son L liquide: soleil, fille'},
    'standard':  {'name': 'Standard',   'icon': '🔤', 'desc': 'Prononciation standard'},
}

AUDIO_DIR = 'gtts_audio'

# ── Step 1: Create categories ────────────────────────────────
print("Creating categories...")
categories = {}
for i, (cls, info) in enumerate(PHONEME_CLASSES.items()):
    cat, created = ExerciseCategory.objects.get_or_create(
        category_type='phoneme',
        name=info['name'],
        defaults={
            'icon':        info['icon'],
            'description': info['desc'],
            'order':       i + 10,
        }
    )
    categories[cls] = cat
    status = '✅ created' if created else '⏭ exists'
    print(f"  {status}: {info['name']}")

# ── Step 2: Parse filenames and create exercises ─────────────
print(f"\nReading files from {AUDIO_DIR}/...")

if not os.path.exists(AUDIO_DIR):
    print(f"❌ Folder '{AUDIO_DIR}' not found! Make sure you run this from the project root.")
    sys.exit(1)

files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
print(f"Found {len(files)} audio files\n")

created_count = 0
skipped_count = 0
error_count   = 0

for filename in sorted(files):
    # Remove extension
    name = filename[:-4]  # remove .mp3

    # Parse: gtts_PHONEME_CLASS_WORD
    # phoneme class can be: nasal, fricative, eu_sound, oi_ui, liquid_l, standard
    found_class = None
    word        = None

    for cls in PHONEME_CLASSES.keys():
        prefix = f'gtts_{cls}_'
        if name.startswith(prefix):
            found_class = cls
            word        = name[len(prefix):]
            break

    if not found_class or not word:
        error_count += 1
        continue

    # Get category for this phoneme class
    category = categories.get(found_class)
    if not category:
        error_count += 1
        continue

    # Create exercise if it doesn't exist
    audio_rel_path = f'{AUDIO_DIR}/{filename}'
    obj, new = Exercise.objects.get_or_create(
        french_text  = word,
        category     = category,
        defaults     = {
            'phoneme_class': found_class,
            'english_text':  '',
            'difficulty':    1,
            'order':         0,
        }
    )
    if new:
        created_count += 1
        if created_count <= 10 or created_count % 100 == 0:
            print(f"  ✅ [{found_class:10s}] {word}")
    else:
        skipped_count += 1

print(f"""
════════════════════════════════════════
✅ Done!
   Created : {created_count} new exercises
   Skipped : {skipped_count} already existed
   Errors  : {error_count} files could not be parsed
   Total   : {Exercise.objects.count()} exercises in database
════════════════════════════════════════
""")

# Print summary per category
print("Summary by phoneme class:")
for cls, cat in categories.items():
    count = Exercise.objects.filter(category=cat).count()
    print(f"  {PHONEME_CLASSES[cls]['icon']} {PHONEME_CLASSES[cls]['name']:12s}: {count} words")
