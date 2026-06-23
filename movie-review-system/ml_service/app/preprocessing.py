"""Text preprocessing for training (see datasets/scripts/) and inference."""

import re


def normalize_text(text: str) -> str:
    """Normalize whitespace and line breaks; preserve casing and punctuation."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\t+", " ", text)
    lines: list[str] = []
    for raw_line in text.split("\n"):
        line = " ".join(raw_line.split())
        if line:
            lines.append(line)
    return "\n".join(lines).strip()


def validate_review_text(text: str) -> str:
    """Return normalized review text or raise if nothing remains."""
    normalized = normalize_text(text)
    if not normalized:
        raise ValueError("Review text is empty after normalization.")
    return normalized


def split_into_sentences(text: str) -> list[str]:
    """Split on sentence-ending punctuation (. ! ?); dependency-light."""
    sentences: list[str] = []
    buf: list[str] = []
    for ch in text:
        buf.append(ch)
        if ch in ".!?":
            piece = "".join(buf).strip()
            if piece:
                sentences.append(piece)
            buf = []
    tail = "".join(buf).strip()
    if tail:
        sentences.append(tail)
    return sentences


def _split_by_char_length(text: str, max_chars: int) -> list[str]:
    if max_chars < 1:
        raise ValueError("max_chars must be at least 1.")
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]


def chunk_text(text: str, max_chars: int) -> list[str]:
    """
    Build sentence-based chunks up to max_chars; oversize sentences are split by length.
    """
    if max_chars < 1:
        raise ValueError("max_chars must be at least 1.")
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    sentences = split_into_sentences(text)
    if not sentences:
        return _split_by_char_length(text, max_chars)

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            if current.strip():
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_by_char_length(sentence, max_chars))
            continue
        sep = 1 if current else 0
        if len(current) + sep + len(sentence) <= max_chars:
            current = f"{current} {sentence}".strip() if current else sentence
        else:
            if current.strip():
                chunks.append(current.strip())
            current = sentence
    if current.strip():
        chunks.append(current.strip())
    return [c for c in chunks if c]


def tokenize_for_inference(text: str) -> list[str]:
    return normalize_text(text).split()
