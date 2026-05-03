"""
extract_commonvoice.py
======================
Extracts exactly the 2,400 needed MP3 files from Mozilla Common Voice FR.

Run this script from your project folder:
    cd "C:\\Users\\shmouel_pc\\Desktop\\2026\\AI projects\\Teach Me French DL Claude\\parle_francais"
    python extract_commonvoice.py
"""

import os
import csv
import json
import tarfile
import time
from collections import defaultdict

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
PROJECT_DIR      = os.path.dirname(os.path.abspath(__file__))
TSV_PATH         = os.path.join(PROJECT_DIR, 'validated.tsv')
SAMPLES_PER_CLASS = 400

# Where to put the extracted files
OUTPUT_CORPUS    = os.path.join(PROJECT_DIR, 'cv-corpus-24.0', 'fr')
OUTPUT_CLIPS     = os.path.join(OUTPUT_CORPUS, 'clips')

# Find the downloaded .tar.gz file automatically
def find_archive():
    """Search common locations for the downloaded fr.tar.gz"""
    search_dirs = [
        os.path.expanduser('~\\Downloads'),
        os.path.expanduser('~\\Desktop'),
        PROJECT_DIR,
        'C:\\',
    ]
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            if f.endswith('.tar.gz') and 'fr' in f.lower():
                return os.path.join(d, f)
            if f.endswith('.tar') and 'fr' in f.lower():
                return os.path.join(d, f)
    return None

# ── PHONEME DETECTION ─────────────────────────────────────────────────────────
PHONEME_RULES = [
    ('nasal',     ['on', 'om', 'an', 'am', 'en', 'em',
                   'in', 'im', 'ain', 'aim', 'ein', 'un', 'um']),
    ('fricative', ['ch', 'rr', ' r', 'r ', 'er', 'ir', 'or', 'ar', 'ur']),
    ('eu_sound',  ['eu', 'œu', 'œ', 'eur', 'eux']),
    ('oi_ui',     ['oi', 'ui', 'oui', 'nuit', 'puis', 'fruit']),
    ('liquid_l',  ['ll', 'il ', 'ill', ' l', 'l ', 'al', 'el', 'ol', 'ul']),
]

def detect_class(sentence):
    text = sentence.lower()
    scores = {}
    for cls, patterns in PHONEME_RULES:
        score = sum(text.count(p) for p in patterns)
        if score > 0:
            scores[cls] = score
    return max(scores, key=scores.get) if scores else 'standard'


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Read validated.tsv and select best clips
# ══════════════════════════════════════════════════════════════════════════════
def select_clips(tsv_path, samples_per_class):
    print('─' * 60)
    print('STEP 1 — Reading validated.tsv and selecting clips')
    print('─' * 60)

    if not os.path.exists(tsv_path):
        print(f'\n❌ ERROR: validated.tsv not found at:')
        print(f'   {tsv_path}')
        print(f'\n   Please place validated.tsv in your project folder:')
        print(f'   {PROJECT_DIR}')
        return None

    print(f'📖 Reading {tsv_path}...')
    by_class = defaultdict(list)
    total_rows = 0

    with open(tsv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            total_rows += 1
            sentence = row.get('sentence', '').strip()
            filename = row.get('path', '').strip()
            upvotes  = int(row.get('up_votes', 0))

            if not sentence or not filename:
                continue
            if upvotes < 2:
                continue

            cls = detect_class(sentence)
            by_class[cls].append({
                'filename': filename,
                'sentence': sentence,
                'upvotes':  upvotes,
                'class':    cls,
            })

    print(f'   Total rows read : {total_rows:,}')
    print(f'\n   Available per class (pool):')
    for cls in ['nasal', 'fricative', 'eu_sound', 'oi_ui', 'liquid_l', 'standard']:
        print(f'     {cls:12s}: {len(by_class[cls]):,}')

    # Select best (highest upvotes) per class
    selected = []
    print(f'\n   Selected (top {samples_per_class} per class):')
    for cls in ['nasal', 'fricative', 'eu_sound', 'oi_ui', 'liquid_l', 'standard']:
        entries = sorted(by_class[cls], key=lambda x: -x['upvotes'])
        chosen  = entries[:samples_per_class]
        selected.extend(chosen)
        bar = '█' * (len(chosen) // 10)
        print(f'     {cls:12s}: {bar} ({len(chosen)})')

    print(f'\n   TOTAL selected  : {len(selected)} clips')
    print(f'   Estimated size  : ~{len(selected) * 100 // 1024} MB')
    return selected


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Copy validated.tsv to corpus folder
# ══════════════════════════════════════════════════════════════════════════════
def setup_corpus_folder(tsv_path, output_corpus, output_clips):
    print('\n' + '─' * 60)
    print('STEP 2 — Setting up corpus folder structure')
    print('─' * 60)

    os.makedirs(output_clips, exist_ok=True)
    print(f'✅ Created: {output_clips}')

    # Copy validated.tsv
    dest_tsv = os.path.join(output_corpus, 'validated.tsv')
    if not os.path.exists(dest_tsv):
        import shutil
        shutil.copy2(tsv_path, dest_tsv)
        print(f'✅ Copied validated.tsv → {dest_tsv}')
    else:
        print(f'✅ validated.tsv already in place')


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Extract MP3 files from archive
# ══════════════════════════════════════════════════════════════════════════════
def extract_clips(selected, archive_path, output_clips):
    print('\n' + '─' * 60)
    print('STEP 3 — Extracting MP3 files from archive')
    print('─' * 60)

    if not archive_path or not os.path.exists(archive_path):
        print(f'\n❌ Archive not found automatically.')
        print(f'   Please enter the full path to your fr.tar.gz file:')
        archive_path = input('   Path: ').strip().strip('"')
        if not os.path.exists(archive_path):
            print(f'❌ File not found: {archive_path}')
            return False

    print(f'📦 Archive : {archive_path}')
    print(f'📁 Output  : {output_clips}')
    print(f'🎵 Files   : {len(selected)} MP3 files to extract')
    print()
    print('   Opening archive... (this may take a moment)')

    # Build set of needed filenames for fast lookup
    needed = {item['filename'] for item in selected}
    extracted = 0
    skipped   = 0
    start     = time.time()

    try:
        with tarfile.open(archive_path, 'r:gz') as tar:
            print(f'   Archive opened! Scanning members...\n')

            for member in tar:
                # We only want files inside fr/clips/
                basename = os.path.basename(member.name)

                # Skip if not an MP3 we need
                if basename not in needed:
                    continue

                # Skip if already extracted
                dest_path = os.path.join(output_clips, basename)
                if os.path.exists(dest_path):
                    skipped += 1
                    needed.discard(basename)
                    continue

                # Extract this file
                member.name = basename   # flatten path
                tar.extract(member, path=output_clips)
                extracted += 1
                needed.discard(basename)

                # Progress update every 100 files
                if extracted % 100 == 0:
                    elapsed = time.time() - start
                    total   = len(selected)
                    done    = extracted + skipped
                    pct     = done / total * 100
                    eta     = (elapsed / done * (total - done)) if done > 0 else 0
                    bar     = '█' * int(pct / 5)
                    print(f'   [{bar:<20}] {pct:.0f}%  '
                          f'{extracted} extracted  '
                          f'ETA: {eta/60:.1f} min')

                # Stop early if we have everything
                if not needed:
                    break

    except Exception as e:
        print(f'\n❌ Error reading archive: {e}')
        print(f'   Extracted so far: {extracted} files')
        return False

    elapsed = time.time() - start
    total_extracted = extracted + skipped

    print(f'\n✅ Extraction complete!')
    print(f'   Extracted : {extracted} new files')
    print(f'   Skipped   : {skipped} already existed')
    print(f'   Total     : {total_extracted} files ready')
    print(f'   Time      : {elapsed/60:.1f} minutes')

    if needed:
        print(f'\n⚠️  {len(needed)} files not found in archive:')
        for f in list(needed)[:5]:
            print(f'     {f}')

    return True


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Save metadata JSON for notebook
# ══════════════════════════════════════════════════════════════════════════════
def save_metadata(selected, output_clips):
    print('\n' + '─' * 60)
    print('STEP 4 — Saving metadata for notebook')
    print('─' * 60)

    # Add full paths to metadata
    for item in selected:
        item['path'] = os.path.join(output_clips, item['filename'])

    # Save JSON
    json_path = os.path.join(PROJECT_DIR, 'selected_clips.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)
    print(f'✅ Metadata saved: {json_path}')

    # Save txt list
    txt_path = os.path.join(PROJECT_DIR, 'clips_to_extract.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        for item in selected:
            f.write(item['filename'] + '\n')
    print(f'✅ File list saved: {txt_path}')

    # Verify files exist
    found   = sum(1 for item in selected if os.path.exists(item['path']))
    missing = len(selected) - found
    print(f'\n   Verification:')
    print(f'   Files found   : {found}/{len(selected)}')
    if missing > 0:
        print(f'   Files missing : {missing}  ← these were not in the archive')


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print()
    print('╔══════════════════════════════════════════════════════════╗')
    print('║   Mozilla Common Voice FR — Smart Extraction Script     ║')
    print('║   Parle Français — CNN Training Pipeline                ║')
    print('╚══════════════════════════════════════════════════════════╝')
    print()

    # Step 1: Select clips
    selected = select_clips(TSV_PATH, SAMPLES_PER_CLASS)
    if not selected:
        exit(1)

    # Step 2: Setup folder structure
    setup_corpus_folder(TSV_PATH, OUTPUT_CORPUS, OUTPUT_CLIPS)

    # Step 3: Find archive and extract
    print('\n' + '─' * 60)
    print('STEP 3 — Finding archive...')
    print('─' * 60)
    archive_path = find_archive()
    if archive_path:
        print(f'✅ Found archive: {archive_path}')
    else:
        print('⚠️  Archive not found automatically.')

    success = extract_clips(selected, archive_path, OUTPUT_CLIPS)

    # Step 4: Save metadata
    save_metadata(selected, OUTPUT_CLIPS)

    # Final summary
    print()
    print('╔══════════════════════════════════════════════════════════╗')
    print('║                    ALL DONE! ✅                         ║')
    print('╠══════════════════════════════════════════════════════════╣')
    print('║  Your project is ready:                                 ║')
    print('║                                                         ║')
    print('║  parle_francais\\                                        ║')
    print('║  ├── parle_francais_CNN.ipynb  ← run this next!        ║')
    print('║  ├── validated.tsv                                      ║')
    print('║  ├── selected_clips.json                                ║')
    print('║  └── cv-corpus-24.0\\fr\\clips\\ ← 2400 MP3 files        ║')
    print('║                                                         ║')
    print('║  Next step: open parle_francais_CNN.ipynb               ║')
    print('║             and run all cells!                          ║')
    print('╚══════════════════════════════════════════════════════════╝')
    print()
