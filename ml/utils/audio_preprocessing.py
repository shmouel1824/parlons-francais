"""
ml/utils/audio_preprocessing.py
────────────────────────────────────────────────────────────────
Converts raw audio (mic recording) → Mel Spectrogram → CNN input tensor

PIPELINE:
    Raw audio bytes (WebM/WAV from browser)
        ↓
    Load with librosa → numpy array [samples]
        ↓
    Resample to 16kHz (standard for speech)
        ↓
    Normalize amplitude
        ↓
    Trim silence at start/end
        ↓
    Compute Mel Spectrogram → [128 mel_bins × T time_frames]
        ↓
    Convert to dB scale (log-mel)
        ↓
    Resize/pad to fixed 128×128
        ↓
    Convert to PyTorch tensor [1, 1, 128, 128]  (batch=1, channels=1)
        ↓
    Ready for CNN input!
────────────────────────────────────────────────────────────────
"""
import io
import numpy as np
import torch

# These will be imported when running the actual project
# pip install librosa soundfile
try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


# ── Constants (match settings.py) ────────────────────────────
SAMPLE_RATE   = 16000     # Hz — standard for speech models
N_MELS        = 128       # mel frequency bins
N_FFT         = 1024      # FFT window size
HOP_LENGTH    = 256       # frames between FFT windows
TARGET_SIZE   = 128       # final spectrogram: 128 × 128
TOP_DB        = 80        # dynamic range for dB conversion


# ─────────────────────────────────────────────────────────────
# MAIN FUNCTION: audio bytes → tensor
# ─────────────────────────────────────────────────────────────
def audio_to_tensor(audio_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> torch.Tensor:
    """
    Full pipeline: raw audio bytes → CNN-ready tensor.

    Args:
        audio_bytes: Raw audio from browser (WebM, WAV, OGG, etc.)
        sample_rate: Target sample rate (default 16kHz)

    Returns:
        torch.Tensor of shape [1, 1, 128, 128]
        (batch=1, channels=1, mel_bins=128, time_frames=128)
    """
    # Step 1: Load audio
    waveform = load_audio(audio_bytes, sample_rate)

    # Step 2: Preprocess
    waveform = normalize_waveform(waveform)
    waveform = trim_silence(waveform, sample_rate)
    waveform = pad_or_trim(waveform, sample_rate, max_duration=3.0)

    # Step 3: Mel spectrogram
    mel_spec = compute_mel_spectrogram(waveform, sample_rate)

    # Step 4: To tensor
    tensor = spectrogram_to_tensor(mel_spec)

    return tensor


def load_audio(audio_bytes: bytes, target_sr: int = SAMPLE_RATE) -> np.ndarray:
    """Load audio bytes into numpy array, resampled to target_sr"""
    if not LIBROSA_AVAILABLE:
        raise ImportError("librosa required: pip install librosa soundfile")

    # librosa.load handles multiple formats (WAV, WebM, OGG, MP3)
    audio_file = io.BytesIO(audio_bytes)
    waveform, sr = librosa.load(audio_file, sr=target_sr, mono=True)
    return waveform


def normalize_waveform(waveform: np.ndarray) -> np.ndarray:
    """Normalize amplitude to [-1, 1]"""
    max_val = np.max(np.abs(waveform))
    if max_val > 0:
        waveform = waveform / max_val
    return waveform


def trim_silence(waveform: np.ndarray, sr: int = SAMPLE_RATE,
                 top_db: int = 20) -> np.ndarray:
    """Remove silence at beginning and end"""
    if not LIBROSA_AVAILABLE:
        return waveform
    waveform, _ = librosa.effects.trim(waveform, top_db=top_db)
    return waveform


def pad_or_trim(waveform: np.ndarray, sr: int = SAMPLE_RATE,
                max_duration: float = 3.0) -> np.ndarray:
    """
    Ensure fixed length audio (pad with zeros or trim to max_duration).
    For letters: 1.0s max
    For words:   2.0s max
    For sentences: 5.0s max (use longer for sentences)
    """
    max_samples = int(sr * max_duration)
    if len(waveform) > max_samples:
        waveform = waveform[:max_samples]
    elif len(waveform) < max_samples:
        # Zero-pad to fixed length
        pad_length = max_samples - len(waveform)
        waveform = np.pad(waveform, (0, pad_length), mode='constant')
    return waveform


def compute_mel_spectrogram(waveform: np.ndarray,
                             sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Compute log-mel spectrogram.

    A mel spectrogram is essentially an image of the audio:
    - X axis: time
    - Y axis: frequency (mel scale — mimics human hearing)
    - Pixel value: amplitude (in dB)

    This is why CNNs work so well for audio:
    the spectrogram IS an image!

    Returns:
        np.ndarray of shape [N_MELS, time_frames]
    """
    if not LIBROSA_AVAILABLE:
        # Return random data for testing without librosa
        return np.random.randn(N_MELS, TARGET_SIZE).astype(np.float32)

    # Compute mel spectrogram
    mel = librosa.feature.melspectrogram(
        y=waveform,
        sr=sr,
        n_mels=N_MELS,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        fmax=sr // 2  # max frequency = Nyquist
    )

    # Convert to dB (log scale) — much better for neural networks
    mel_db = librosa.power_to_db(mel, ref=np.max, top_db=TOP_DB)

    return mel_db.astype(np.float32)


def spectrogram_to_tensor(mel_spec: np.ndarray,
                           target_size: int = TARGET_SIZE) -> torch.Tensor:
    """
    Resize spectrogram to fixed TARGET_SIZE × TARGET_SIZE,
    then convert to PyTorch tensor.

    Shape transformation:
        [128, T]       → resize T dimension
        [128, 128]     → fixed size
        [1, 128, 128]  → add channel dim
        [1, 1, 128, 128] → add batch dim
    """
    # Resize time dimension to target_size using linear interpolation
    if mel_spec.shape[1] != target_size:
        # Simple interpolation along time axis
        from PIL import Image
        img = Image.fromarray(mel_spec)
        img = img.resize((target_size, N_MELS), Image.BILINEAR)
        mel_spec = np.array(img)

    # Normalize to [0, 1]
    mel_min, mel_max = mel_spec.min(), mel_spec.max()
    if mel_max > mel_min:
        mel_spec = (mel_spec - mel_min) / (mel_max - mel_min)

    # Convert to tensor [1, 1, 128, 128]
    tensor = torch.from_numpy(mel_spec).float()
    tensor = tensor.unsqueeze(0).unsqueeze(0)  # [1, 1, H, W]

    return tensor


# ─────────────────────────────────────────────────────────────
# VISUALIZATION HELPER (for teaching/debugging)
# ─────────────────────────────────────────────────────────────
def save_spectrogram_image(mel_spec: np.ndarray, output_path: str):
    """
    Save mel spectrogram as PNG image.
    Useful for teaching: shows students what their speech looks like!
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        plt.figure(figsize=(8, 4))
        plt.imshow(mel_spec, aspect='auto', origin='lower',
                   cmap='magma', interpolation='nearest')
        plt.colorbar(format='%+2.0f dB')
        plt.title('Mel Spectrogram of Your Pronunciation')
        plt.xlabel('Time frames')
        plt.ylabel('Mel frequency bins')
        plt.tight_layout()
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
    except ImportError:
        pass  # matplotlib optional


# ─────────────────────────────────────────────────────────────
# PHONEME SEGMENTATION
# ─────────────────────────────────────────────────────────────
def segment_phonemes(waveform: np.ndarray, sr: int = SAMPLE_RATE,
                     window_duration: float = 0.1) -> list:
    """
    Split audio into short windows, each window gets scored independently.
    This gives per-phoneme feedback (which parts were correct/incorrect).

    Returns list of (start_time, end_time, tensor) tuples.
    """
    window_samples = int(sr * window_duration)
    hop_samples = window_samples // 2  # 50% overlap

    segments = []
    for start in range(0, len(waveform) - window_samples, hop_samples):
        end = start + window_samples
        segment = waveform[start:end]
        mel = compute_mel_spectrogram(segment, sr)
        tensor = spectrogram_to_tensor(mel)
        segments.append({
            'start_time': start / sr,
            'end_time': end / sr,
            'tensor': tensor,
        })
    return segments
