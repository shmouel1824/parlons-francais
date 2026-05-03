"""
extract_commonvoice_v2.py
=========================
Extracts 4,800 MP3 files from Mozilla Common Voice FR.

Improvements over v1:
  Fix 1 — 800 samples/class instead of 400
  Fix 2 — dominance threshold: rejects ambiguous sentences

Run from your project folder:
    cd "C:\\Users\\shmouel_pc\\Desktop\\2026\\AI projects\\Teach Me French DL Claude\\parle_francais"
    python extract_commonvoice_v2.py
"""

import os, csv, json, tarfile, time, random
from collections import defaultdict

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
PROJECT_DIR       = os.path.dirname(os.path.abspath(__file__))
TSV_PATH          = os.path.join(PROJECT_DIR, 'validated.tsv')
SAMPLES_PER_CLASS = 800          # Fix 1: was 400
DOMINANCE_THRESH  = 0.55         # Fix 2: reject if winner scores < 55%

OUTPUT_CORPUS     = os.path.join(PROJECT_DIR, 'cv-corpus-24.0', 'fr')
OUTPUT_CLIPS      = os.path.join(OUTPUT_CORPUS, 'clips')

# ── FIX 2: IMPROVED PHONEME DETECTION ─────────────────────────────────────────
PHONEME_RULES = [
    ('nasal',     ['ɔ̃', 'ɑ̃', 'ɛ̃',
                   'on', 'om', 'an', 'am', 'en', 'em',
                   'in', 'im', 'ain', 'aim', 'ein', 'un', 'um']),
    ('fricative', ['ch', ' r', 'r ', 'er ', ' er', 'ir ',
                   'our', 'ar ', ' ar', 'rr']),
    ('eu_sound',  ['eur', 'eux', 'euse', 'œur', 'œu',
                   'feu', 'bleu', 'deux', 'peu', 'jeu', 'eu ']),
    ('oi_ui',     ['oir', 'ois', 'oit', 'oix', 'oie',
                   'nuit', 'fruit', 'bruit', 'pluie', ' ui',
                   'oi ', ' oi']),
    ('liquid_l',  ['ll', 'ill', 'eil', 'ail', 'euil',
                   'al ', 'el ', 'ol ', ' la', ' le', ' li', ' lo', ' lu']),
]

def detect_class(sentence):
    """
    Returns (class, dominance) or (None, dominance) if ambiguous.
    Fix 2: only accepts sentences where one class clearly dominates.
    """
    text   = sentence.lower()
    scores = {}

    for cls, patterns in PHONEME_RULES:
        score = sum(text.count(p) for p in patterns)
        if score > 0:
            scores[cls] = score

    if not scores:
        return 'standard', 1.0    # no special phoneme → clearly standard

    total     = sum(scores.values())
    winner    = max(scores, key=scores.get)
    dominance = scores[winner] / total

    if dominance < DOMINANCE_THRESH:
        return None, dominance    # ambiguous → reject

    return winner, dominance


# ── FIND ARCHIVE ──────────────────────────────────────────────────────────────
def find_archive():
    search_dirs = [
        os.path.expanduser('~\\Downloads'),
        os.path.expanduser('~\\Desktop'),
        PROJECT_DIR,
    ]
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if (f.endswith('.tar.gz') or f.endswith('.tar')) and 'fr' in f.lower():
                return os.path.join(d, f)
    return None


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Read TSV and select clips
# ══════════════════════════════════════════════════════════════════════════════
def select_clips():
    print('─' * 65)
    print('STEP 1 — Reading validated.tsv with dominance filtering (Fix 2)')
    print('─' * 65)

    if not os.path.exists(TSV_PATH):
        print(f'\n❌ validated.tsv not found at: {TSV_PATH}')
        return None

    print(f'📖 Reading {TSV_PATH}...')

    by_class   = defaultdict(list)
    total_rows = 0
    rejected   = 0

    with open(TSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            total_rows += 1
            sentence = row.get('sentence', '').strip()
            filename = row.get('path',     '').strip()
            upvotes  = int(row.get('up_votes', 0))

            if not sentence or not filename:
                continue
            if upvotes < 2:
                continue

            cls, dominance = detect_class(sentence)

            if cls is None:
                rejected += 1    # Fix 2: reject ambiguous sentences
                continue

            by_class[cls].append({
                'filename':  filename,
                'sentence':  sentence,
                'upvotes':   upvotes,
                'dominance': round(dominance, 3),
                'class':     cls,
            })

    print(f'\n   Total rows read  : {total_rows:,}')
    print(f'   Rejected (ambig) : {rejected:,}  ← Fix 2 in action!')
    print(f'\n   Available per class after filtering:')
    for cls in ['nasal', 'fricative', 'eu_sound', 'oi_ui', 'liquid_l', 'standard']:
        print(f'     {cls:12s}: {len(by_class[cls]):,}')

    # Select best (highest dominance, then upvotes)
    selected = []
    print(f'\n   Selecting top {SAMPLES_PER_CLASS} per class:')
    for cls in ['nasal', 'fricative', 'eu_sound', 'oi_ui', 'liquid_l', 'standard']:
        entries = sorted(by_class[cls],
                         key=lambda x: (-x['dominance'], -x['upvotes']))
        chosen  = entries[:SAMPLES_PER_CLASS]
        selected.extend(chosen)
        bar = '█' * (len(chosen) // 20)
        avg_dom = sum(e['dominance'] for e in chosen) / len(chosen) if chosen else 0
        print(f'     {cls:12s}: {bar} ({len(chosen)})  avg dominance: {avg_dom:.0%}')

    print(f'\n   TOTAL selected   : {len(selected)} clips  (Fix 1: was 2,400)')
    print(f'   Estimated size   : ~{len(selected) * 100 // 1024} MB')

    return selected


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Setup folder structure
# ══════════════════════════════════════════════════════════════════════════════
def setup_folders():
    print('\n' + '─' * 65)
    print('STEP 2 — Setting up folder structure')
    print('─' * 65)

    os.makedirs(OUTPUT_CLIPS, exist_ok=True)
    print(f'✅ Clips folder: {OUTPUT_CLIPS}')

    # Copy validated.tsv
    import shutil
    dest_tsv = os.path.join(OUTPUT_CORPUS, 'validated.tsv')
    if not os.path.exists(dest_tsv):
        shutil.copy2(TSV_PATH, dest_tsv)
        print(f'✅ Copied validated.tsv → corpus folder')
    else:
        print(f'✅ validated.tsv already in corpus folder')


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Extract MP3 files
# ══════════════════════════════════════════════════════════════════════════════
def extract_clips(selected, archive_path):
    print('\n' + '─' * 65)
    print('STEP 3 — Extracting MP3 files from archive')
    print('─' * 65)

    if not archive_path or not os.path.exists(archive_path):
        print('⚠️  Archive not found automatically.')
        print('   Please enter full path to your fr.tar.gz:')
        archive_path = input('   Path: ').strip().strip('"')
        if not os.path.exists(archive_path):
            print(f'❌ Not found: {archive_path}')
            return False

    print(f'📦 Archive : {archive_path}')
    print(f'📁 Output  : {OUTPUT_CLIPS}')
    print(f'🎵 Files   : {len(selected)} to extract')

    needed    = {item['filename'] for item in selected}
    extracted = 0
    skipped   = 0
    start     = time.time()

    # Count already extracted
    for filename in list(needed):
        if os.path.exists(os.path.join(OUTPUT_CLIPS, filename)):
            skipped += 1
            needed.discard(filename)

    if skipped:
        print(f'   Already extracted: {skipped} files (skipped)')

    if not needed:
        print('✅ All files already extracted!')
        return True

    print(f'   Extracting {len(needed)} new files...\n')

    try:
        with tarfile.open(archive_path, 'r:gz') as tar:
            print('   Archive opened! Scanning...\n')
            for member in tar:
                basename = os.path.basename(member.name)
                if basename not in needed:
                    continue

                dest_path  = os.path.join(OUTPUT_CLIPS, basename)
                member.name = basename
                tar.extract(member, path=OUTPUT_CLIPS)
                extracted += 1
                needed.discard(basename)

                if extracted % 200 == 0:
                    elapsed = time.time() - start
                    total   = len(selected) - skipped
                    pct     = extracted / total * 100 if total > 0 else 100
                    eta     = elapsed / extracted * (total - extracted)
                    bar     = '█' * int(pct / 5)
                    print(f'   [{bar:<20}] {pct:.0f}%  '
                          f'{extracted}/{total}  '
                          f'ETA: {eta/60:.1f} min')

                if not needed:
                    break

    except Exception as e:
        print(f'\n❌ Error: {e}')
        return False

    elapsed = time.time() - start
    print(f'\n✅ Extraction complete!')
    print(f'   New files     : {extracted}')
    print(f'   Already had   : {skipped}')
    print(f'   Total ready   : {extracted + skipped}')
    print(f'   Time          : {elapsed/60:.1f} minutes')

    if needed:
        print(f'\n⚠️  {len(needed)} files not found in archive')

    return True


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Save metadata JSON
# ══════════════════════════════════════════════════════════════════════════════
def save_metadata(selected):
    print('\n' + '─' * 65)
    print('STEP 4 — Saving selected_clips_v2.json')
    print('─' * 65)

    for item in selected:
        item['path'] = os.path.join(OUTPUT_CLIPS, item['filename'])

    json_path = os.path.join(PROJECT_DIR, 'selected_clips_v2.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)
    print(f'✅ Saved: {json_path}')

    # Verify
    found   = sum(1 for item in selected if os.path.exists(item['path']))
    missing = len(selected) - found
    print(f'\n   Verification:')
    print(f'   Files found   : {found}/{len(selected)}')
    if missing:
        print(f'   Files missing : {missing}')
    else:
        print(f'   ✅ All files verified!')

    # Distribution summary
    from collections import Counter
    dist = Counter(i['class'] for i in selected)
    print(f'\n   Final distribution:')
    for cls, count in sorted(dist.items()):
        bar = '█' * (count // 20)
        print(f'     {cls:12s}: {bar} ({count})')


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print()
    print('╔═══════════════════════════════════════════════════════════════╗')
    print('║   Mozilla Common Voice FR — Extract Script v2               ║')
    print('║                                                             ║')
    print('║   Fix 1: 800 samples/class  (was 400)                      ║')
    print('║   Fix 2: dominance threshold (reject ambiguous sentences)   ║')
    print('╚═══════════════════════════════════════════════════════════════╝')
    print()

    selected = select_clips()
    if not selected:
        exit(1)

    setup_folders()

    archive_path = find_archive()
    if archive_path:
        print(f'\n✅ Found archive automatically: {archive_path}')
    else:
        print('\n⚠️  Archive not found automatically.')

    success = extract_clips(selected, archive_path)
    save_metadata(selected)

    print()
    print('╔═══════════════════════════════════════════════════════════════╗')
    print('║                    ALL DONE! ✅                             ║')
    print('╠═══════════════════════════════════════════════════════════════╣')
    print('║  Files ready:                                               ║')
    print('║    selected_clips_v2.json  ← notebook reads this           ║')
    print('║    cv-corpus-24.0/fr/clips/ ← 4,800 MP3 files              ║')
    print('║                                                             ║')
    print('║  Next: open parle_francais_CNN_v2.ipynb and run all cells! ║')
    print('╚═══════════════════════════════════════════════════════════════╝')
    print()
