"""Local, offline embeddings for the vector leg (Phase 1b).

Uses model2vec static embeddings (numpy-based, no onnxruntime) — chosen over
the originally-planned fastembed because fastembed/onnxruntime ship no cp314
wheels, and the only interpreter on this machine with `enable_load_extension`
(required by sqlite-vec) is Homebrew python 3.14. model2vec is local, free,
and fully offline after a one-time model download. Pinned for vector
comparability: minishlab/potion-base-8M (256-dim).

Nothing here touches the network except model2vec's one-time model fetch
(inbound model weights — no repo content egress; consistent with the no-egress
HARD DECISION). Set HF_HUB_OFFLINE=1 to force cache-only.
"""

from __future__ import annotations

MODEL_ID = "minishlab/potion-base-8M"
DIM = 256


def available() -> bool:
    try:
        import model2vec  # noqa: F401
        return True
    except Exception:
        return False


_MODEL = None


def _model():
    global _MODEL
    if _MODEL is None:
        from model2vec import StaticModel
        _MODEL = StaticModel.from_pretrained(MODEL_ID)
    return _MODEL


def embed(texts: list[str]) -> list[list[float]]:
    """Return one DIM-length float vector per input text."""
    if not texts:
        return []
    vecs = _model().encode(list(texts))
    return [[float(x) for x in row] for row in vecs]


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
