"""
ml/models/cnn_models.py  (TensorFlow / Keras version)
─────────────────────────────────────────────────────────────────
TWO CNN MODELS:

  1. PhonemeNet  — classifies French phonemes + scores pronunciation
  2. SpeakerNet  — extracts voice embedding for voice-password login

Both work on MEL SPECTROGRAMS (audio treated as 2D image).

FRAMEWORK: TensorFlow 2.15 / Keras
─────────────────────────────────────────────────────────────────
"""
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
import numpy as np


# ─────────────────────────────────────────────────────────────
# ALL 37 FRENCH PHONEMES
# ─────────────────────────────────────────────────────────────
FRENCH_PHONEMES = [
    # Oral vowels
    'a', 'e', 'ɛ', 'i', 'o', 'ɔ', 'u', 'y', 'ø', 'œ', 'ə',
    # Nasal vowels  ← the hardest French sounds!
    'ɑ̃', 'ɔ̃', 'ɛ̃', 'œ̃',
    # Semi-vowels
    'j', 'w', 'ɥ',
    # Plosive consonants
    'p', 'b', 't', 'd', 'k', 'ɡ',
    # Fricative consonants
    'f', 'v', 's', 'z', 'ʃ', 'ʒ',
    # Nasal consonants
    'm', 'n', 'ɲ', 'ŋ',
    # Liquid consonants
    'l', 'ʁ',
    # Silence/boundary
    '<SIL>',
]
NUM_PHONEMES = len(FRENCH_PHONEMES)   # 37


# ─────────────────────────────────────────────────────────────
# SHARED BUILDING BLOCK: ConvBlock
# ─────────────────────────────────────────────────────────────
def conv_block(x, filters, kernel_size=3, pool_size=2, dropout_rate=0.1):
    """
    One convolutional block:
        Conv2D → BatchNormalization → ReLU → MaxPool2D → Dropout

    This is the fundamental unit repeated 4 times in both CNNs.

    Args:
        x           : input tensor
        filters     : number of convolutional filters (32, 64, 128, 256)
        kernel_size : size of the convolution kernel (default 3×3)
        pool_size   : max pooling size (default 2×2 → halves dimensions)
        dropout_rate: spatial dropout probability

    Returns:
        output tensor (half the spatial size of input)
    """
    x = layers.Conv2D(
        filters=filters,
        kernel_size=kernel_size,
        padding='same',           # keep spatial size before pooling
        use_bias=False,           # bias not needed before BatchNorm
    )(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    x = layers.MaxPooling2D(pool_size=pool_size)(x)
    x = layers.SpatialDropout2D(dropout_rate)(x)
    return x


# ─────────────────────────────────────────────────────────────
# MODEL 1: PhonemeNet
# ─────────────────────────────────────────────────────────────
def build_phoneme_net(num_phonemes=NUM_PHONEMES, dropout=0.3):
    """
    Builds the PhonemeNet model.

    ARCHITECTURE:
    ┌─────────────────────────────────────────────────┐
    │  Input: [128, 128, 1]  ← mel spectrogram        │
    │                                                 │
    │  ConvBlock(32)   → [64, 64, 32]                 │
    │  ConvBlock(64)   → [32, 32, 64]                 │
    │  ConvBlock(128)  → [16, 16, 128]                │
    │  ConvBlock(256)  → [8,  8,  256]                │
    │                                                 │
    │  GlobalAveragePooling2D  → [256]                │
    │                                                 │
    │  Dense(512) → BN → ReLU → Dropout               │
    │  Dense(256) → BN → ReLU → Dropout               │
    │                                                 │
    │  ┌── Head A: Dense(37)  → phoneme class         │
    │  └── Head B: Dense(1) + Sigmoid → score 0–1     │
    └─────────────────────────────────────────────────┘

    INPUTS:
        Mel spectrogram image: shape (128, 128, 1)

    OUTPUTS:
        phoneme_output : shape (num_phonemes,) — which phoneme?
        score_output   : shape (1,) — quality score 0.0–1.0

    TRAINING:
        Loss = CrossEntropy(phoneme) + MSE(score)
    """
    # ── Input ──────────────────────────────────────────────
    inputs = keras.Input(shape=(128, 128, 1), name='mel_spectrogram')

    # ── Feature Extraction (4 conv blocks) ─────────────────
    x = conv_block(inputs, filters=32,  pool_size=2, dropout_rate=0.1)   # → 64×64
    x = conv_block(x,      filters=64,  pool_size=2, dropout_rate=0.1)   # → 32×32
    x = conv_block(x,      filters=128, pool_size=2, dropout_rate=0.2)   # → 16×16
    x = conv_block(x,      filters=256, pool_size=2, dropout_rate=0.2)   # →  8×8

    # ── Global Average Pooling: [8, 8, 256] → [256] ────────
    x = layers.GlobalAveragePooling2D(name='gap')(x)

    # ── Shared Dense Layers ─────────────────────────────────
    x = layers.Dense(512, use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    x = layers.Dropout(dropout)(x)

    x = layers.Dense(256, use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    shared = layers.Dropout(dropout, name='shared_features')(x)

    # ── Head A: Phoneme Classifier ──────────────────────────
    phoneme_output = layers.Dense(
        num_phonemes,
        activation='softmax',
        name='phoneme_output'
    )(shared)

    # ── Head B: Pronunciation Quality Score ─────────────────
    score_x = layers.Dense(64, activation='relu')(shared)
    score_output = layers.Dense(
        1,
        activation='sigmoid',
        name='score_output'
    )(score_x)

    # ── Build Model ─────────────────────────────────────────
    model = Model(
        inputs=inputs,
        outputs={'phoneme_output': phoneme_output,
                 'score_output': score_output},
        name='PhonemeNet'
    )
    return model


def compile_phoneme_net(model, learning_rate=3e-4):
    """Compile PhonemeNet with appropriate losses and metrics"""
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss={
            'phoneme_output': 'sparse_categorical_crossentropy',
            'score_output':   'mse',
        },
        loss_weights={
            'phoneme_output': 1.0,
            'score_output':   2.0,    # weight score loss more
        },
        metrics={
            'phoneme_output': ['accuracy'],
            'score_output':   ['mae'],
        }
    )
    return model


# ─────────────────────────────────────────────────────────────
# MODEL 2: SpeakerNet
# ─────────────────────────────────────────────────────────────
def build_speaker_net(embedding_dim=128):
    """
    Builds the SpeakerNet model for voice authentication.

    ARCHITECTURE:
    ┌─────────────────────────────────────────────────┐
    │  Input: [128, 128, 1]  ← mel spectrogram        │
    │                                                 │
    │  ConvBlock(32)  → [64, 64, 32]                  │
    │  ConvBlock(64)  → [32, 32, 64]                  │
    │  ConvBlock(128) → [16, 16, 128]                 │
    │  ConvBlock(256) → [8,  8,  256]                 │
    │                                                 │
    │  GlobalAveragePooling2D  → [256]                │
    │                                                 │
    │  Dense(256) → BN → ReLU → Dropout(0.2)          │
    │  Dense(128)                                     │
    │  L2 Normalize  ← important!                     │
    │                                                 │
    │  Output: embedding [128]                        │
    │  (your unique voice "fingerprint")              │
    └─────────────────────────────────────────────────┘

    HOW VOICE LOGIN WORKS:
        Register:
            speak "bonjour" → SpeakerNet → embedding_A  → save to DB
        Login:
            speak "bonjour" → SpeakerNet → embedding_B
            cosine_similarity(embedding_A, embedding_B) → 0.0 to 1.0
            if similarity >= 0.82 → ✓ authenticated

    TRAINING with Triplet Loss:
        anchor   = your voice recording 1
        positive = your voice recording 2 (same speaker → embeddings close)
        negative = another person's voice  (different speaker → embeddings far)
    """
    inputs = keras.Input(shape=(128, 128, 1), name='mel_spectrogram')

    # ── Feature Extraction ──────────────────────────────────
    x = conv_block(inputs, filters=32,  pool_size=2, dropout_rate=0.1)
    x = conv_block(x,      filters=64,  pool_size=2, dropout_rate=0.1)
    x = conv_block(x,      filters=128, pool_size=2, dropout_rate=0.2)
    x = conv_block(x,      filters=256, pool_size=2, dropout_rate=0.2)

    x = layers.GlobalAveragePooling2D(name='gap')(x)

    # ── Projection to Embedding Space ───────────────────────
    x = layers.Dense(256, use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    x = layers.Dropout(0.2)(x)

    x = layers.Dense(embedding_dim, name='embedding_raw')(x)

    # ── L2 Normalization ← makes cosine similarity = dot product ──
    embedding = layers.Lambda(
        lambda t: tf.math.l2_normalize(t, axis=1),
        name='embedding'
    )(x)

    model = Model(inputs=inputs, outputs=embedding, name='SpeakerNet')
    return model


# ─────────────────────────────────────────────────────────────
# TRIPLET LOSS for SpeakerNet training
# ─────────────────────────────────────────────────────────────
class TripletLoss(keras.losses.Loss):
    """
    Triplet loss for training SpeakerNet.

    The goal: in the embedding space,
        - same speaker recordings should be CLOSE together
        - different speaker recordings should be FAR apart

    loss = max(0, dist(anchor, positive) - dist(anchor, negative) + margin)

    anchor   = recording of speaker A (any sample)
    positive = another recording of speaker A (same person)
    negative = recording of speaker B (different person)

    margin   = minimum distance gap we enforce (default 0.3)
    """
    def __init__(self, margin=0.3, **kwargs):
        super().__init__(**kwargs)
        self.margin = margin

    def call(self, y_true, y_pred):
        # y_pred shape: [batch*3, embedding_dim]
        # First third = anchors, second = positives, third = negatives
        batch = tf.shape(y_pred)[0] // 3
        anchors  = y_pred[:batch]
        positives = y_pred[batch:batch*2]
        negatives = y_pred[batch*2:]

        # Euclidean distances
        dist_pos = tf.reduce_sum(tf.square(anchors - positives), axis=1)
        dist_neg = tf.reduce_sum(tf.square(anchors - negatives), axis=1)

        loss = tf.maximum(0.0, dist_pos - dist_neg + self.margin)
        return tf.reduce_mean(loss)


# ─────────────────────────────────────────────────────────────
# COSINE SIMILARITY HELPER
# ─────────────────────────────────────────────────────────────
def cosine_similarity(embedding_a: np.ndarray,
                      embedding_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two voice embeddings.
    Since embeddings are L2-normalized, this equals the dot product.

    Returns float in [0, 1]:
        ~1.0 = same speaker
        ~0.0 = different speakers
        threshold: 0.82 = authenticated
    """
    a = embedding_a / (np.linalg.norm(embedding_a) + 1e-8)
    b = embedding_b / (np.linalg.norm(embedding_b) + 1e-8)
    return float(np.dot(a, b))


# ─────────────────────────────────────────────────────────────
# QUICK TEST — run this file directly to verify models build
# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Building PhonemeNet...")
    phoneme_net = build_phoneme_net()
    phoneme_net.summary()

    print("\nBuilding SpeakerNet...")
    speaker_net = build_speaker_net()
    speaker_net.summary()

    # Test with dummy input
    dummy = np.random.randn(2, 128, 128, 1).astype(np.float32)

    outputs = phoneme_net(dummy, training=False)
    print(f"\nPhonemeNet output shapes:")
    print(f"  phoneme_output: {outputs['phoneme_output'].shape}")   # (2, 37)
    print(f"  score_output:   {outputs['score_output'].shape}")     # (2, 1)

    emb = speaker_net(dummy, training=False)
    print(f"\nSpeakerNet embedding shape: {emb.shape}")              # (2, 128)

    # Test cosine similarity
    sim = cosine_similarity(emb[0].numpy(), emb[1].numpy())
    print(f"Cosine similarity (random test): {sim:.4f}")

    print("\n✓ All models built successfully!")
