import pytest

from app.preprocessing import (
    chunk_text,
    normalize_text,
    split_into_sentences,
    validate_review_text,
)


def test_normalize_text_whitespace() -> None:
    assert normalize_text("  a  b  \n\n c\t\t d  ") == "a b\nc d"


def test_validate_review_text_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        validate_review_text("   \n\t  ")


def test_split_into_sentences() -> None:
    s = split_into_sentences("Первое. Второе! Третье? Четвёртое")
    assert len(s) == 4
    assert s[0].endswith(".")
    assert "!" in s[1]


def test_chunk_text_short() -> None:
    t = "Короткий текст."
    assert chunk_text(t, 900) == [t.strip()]


def test_chunk_text_respects_max_length() -> None:
    text = "Short one. Second sentence here. Third."
    chunks = chunk_text(text, 18)
    assert chunks
    assert all(len(c) <= 18 for c in chunks)


def test_chunk_text_oversized_sentence() -> None:
    long = "Z" * 250
    chunks = chunk_text(long, 100)
    assert chunks == ["Z" * 100, "Z" * 100, "Z" * 50]
