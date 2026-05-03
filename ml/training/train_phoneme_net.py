"""
ml/training/train_phoneme_net.py
────────────────────────────────────────────────────────────────
Training script for PhonemeNet CNN.

DATASET: Mozilla Common Voice (French)
    Download: https://commonvoice.mozilla.org/fr/datasets
    Size: ~800 hours of French speech
    Format: MP3 files + TSV metadata

USAGE:
    # 1. Download dataset to ml/data/cv-corpus-fr/
    # 2. Run:
    python ml/training/train_phoneme_net.py

TRAINING STRATEGY:
    Phase 1: Train on clean, studio-quality recordings (SIWIS dataset)
    Phase 2: Fine-tune on Common Voice (noisy, natural speech)
    Phase 3: Fine-tune on student recordings collected from the app

This 3-phase approach gives the best results because:
    - Phase 1 teaches clean phoneme patterns
    - Phase 2 generalizes to real-world speech
    - Phase 3 adapts to learner pronunciation errors
────────────────────────────────────────────────────────────────
"""
import os
import sys
import torch
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ml.models.cnn_models import PhonemeNet, PhonemeNetLoss
from ml.utils.audio_preprocessing import audio_to_tensor

# ── Config ────────────────────────────────────────────────────
BATCH_SIZE    = 32
EPOCHS        = 50
LEARNING_RATE = 3e-4
DATA_DIR      = Path('ml/data')
MODEL_SAVE    = Path('ml/models/phoneme_cnn.pth')
DEVICE        = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

print(f"Training on: {DEVICE}")


# ─────────────────────────────────────────────────────────────
# DATASET
# ─────────────────────────────────────────────────────────────
class FrenchPhonemeDataset(Dataset):
    """
    Loads French audio files and their phoneme labels.

    Expected structure:
        ml/data/
            phoneme_a/       ← folder name = phoneme label
                clip_001.wav
                clip_002.wav
            phoneme_ɔ̃/
                ...
            ...

    We segment each audio file into windows and label each
    window with the dominant phoneme.
    """

    def __init__(self, data_dir: Path, augment: bool = False):
        self.samples = []      # list of (tensor, phoneme_idx, score_target)
        self.augment = augment

        phoneme_to_idx = {p: i for i, p in enumerate(PhonemeNet.FRENCH_PHONEMES)}

        # Walk data directory
        for phoneme_dir in sorted(data_dir.iterdir()):
            if not phoneme_dir.is_dir():
                continue

            # Extract phoneme from directory name (e.g. "phoneme_ɔ̃" → "ɔ̃")
            phoneme = phoneme_dir.name.replace('phoneme_', '')
            if phoneme not in phoneme_to_idx:
                continue

            phoneme_idx = phoneme_to_idx[phoneme]

            for audio_file in phoneme_dir.glob('*.wav'):
                self.samples.append({
                    'path': audio_file,
                    'phoneme_idx': phoneme_idx,
                    'score_target': 1.0,  # all training data = perfect pronunciation
                })

        print(f"Dataset: {len(self.samples)} samples loaded")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]

        # Load and preprocess audio → tensor
        with open(sample['path'], 'rb') as f:
            audio_bytes = f.read()

        try:
            tensor = audio_to_tensor(audio_bytes)
        except Exception:
            # Return zero tensor if audio fails to load
            tensor = torch.zeros(1, 1, 128, 128)

        tensor = tensor.squeeze(0)  # Remove batch dim: [1, 128, 128]

        # Augmentation for training
        if self.augment:
            tensor = self._augment(tensor)

        phoneme_idx = torch.tensor(sample['phoneme_idx'], dtype=torch.long)
        score = torch.tensor([[sample['score_target']]], dtype=torch.float)

        return tensor, phoneme_idx, score

    def _augment(self, tensor):
        """
        Data augmentation to improve generalization.
        Applies random perturbations to the spectrogram.
        """
        # SpecAugment: mask random time/frequency bands
        _, H, W = tensor.shape

        # Frequency masking (mask random mel bins)
        f = np.random.randint(0, H // 8)
        f0 = np.random.randint(0, H - f)
        tensor[0, f0:f0+f, :] = 0

        # Time masking (mask random time steps)
        t = np.random.randint(0, W // 8)
        t0 = np.random.randint(0, W - t)
        tensor[0, :, t0:t0+t] = 0

        # Random noise
        tensor = tensor + torch.randn_like(tensor) * 0.02

        return tensor


# ─────────────────────────────────────────────────────────────
# TRAINING LOOP
# ─────────────────────────────────────────────────────────────
def train():
    # Load dataset
    data_dir = DATA_DIR / 'phonemes'
    if not data_dir.exists():
        print(f"\n⚠ Data directory not found: {data_dir}")
        print("  Please download French phoneme data to ml/data/phonemes/")
        print("  Expected structure: ml/data/phonemes/phoneme_a/clip_001.wav ...")
        print("\n  Quick start: use Mozilla Common Voice FR dataset")
        print("  https://commonvoice.mozilla.org/fr/datasets")
        return

    dataset = FrenchPhonemeDataset(data_dir, augment=True)

    # Split train/validation 80/20
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=4)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

    # Model, loss, optimizer
    model = PhonemeNet().to(DEVICE)
    criterion = PhonemeNetLoss(phoneme_weight=1.0, score_weight=2.0)
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

    best_val_acc = 0.0

    print(f"\nStarting training: {EPOCHS} epochs, batch={BATCH_SIZE}")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    print("─" * 60)

    for epoch in range(1, EPOCHS + 1):
        # ── Training ──────────────────────────────────────
        model.train()
        train_loss, train_correct, train_total = 0, 0, 0

        for tensors, phoneme_targets, score_targets in train_loader:
            tensors = tensors.to(DEVICE)
            phoneme_targets = phoneme_targets.to(DEVICE)
            score_targets = score_targets.to(DEVICE)

            optimizer.zero_grad()
            phoneme_logits, score_pred = model(tensors)
            loss, _, _ = criterion(phoneme_logits, score_pred,
                                   phoneme_targets, score_targets)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            train_loss += loss.item()
            preds = phoneme_logits.argmax(dim=1)
            train_correct += (preds == phoneme_targets).sum().item()
            train_total += len(phoneme_targets)

        train_acc = train_correct / train_total * 100

        # ── Validation ────────────────────────────────────
        model.eval()
        val_loss, val_correct, val_total = 0, 0, 0

        with torch.no_grad():
            for tensors, phoneme_targets, score_targets in val_loader:
                tensors = tensors.to(DEVICE)
                phoneme_targets = phoneme_targets.to(DEVICE)
                score_targets = score_targets.to(DEVICE)

                phoneme_logits, score_pred = model(tensors)
                loss, _, _ = criterion(phoneme_logits, score_pred,
                                       phoneme_targets, score_targets)
                val_loss += loss.item()
                preds = phoneme_logits.argmax(dim=1)
                val_correct += (preds == phoneme_targets).sum().item()
                val_total += len(phoneme_targets)

        val_acc = val_correct / val_total * 100
        scheduler.step(val_loss)

        print(f"Epoch {epoch:3d}/{EPOCHS} | "
              f"Train Loss: {train_loss/len(train_loader):.4f} | "
              f"Train Acc: {train_acc:.1f}% | "
              f"Val Acc: {val_acc:.1f}%")

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            MODEL_SAVE.parent.mkdir(exist_ok=True)
            torch.save(model.state_dict(), MODEL_SAVE)
            print(f"  ✓ New best model saved! ({val_acc:.1f}%)")

    print(f"\nTraining complete. Best validation accuracy: {best_val_acc:.1f}%")
    print(f"Model saved to: {MODEL_SAVE}")


if __name__ == '__main__':
    train()
