import re
from html import unescape
from typing import Any, TypeVar

from slugify import slugify as base_slugify

SQUARE_BRACKETS_PATTERN = re.compile(r"\[.*?]")
HTML_TAG_PATTERN = re.compile(r"<.*?>")
SPEAKER_PATTERN = re.compile(r"^[\[\w -\]]{3,20}: ", re.UNICODE | re.MULTILINE)
SEPARATE_NUMBER_PATTERN = re.compile(r"\s[0-9]+\s")
REPEATED_EMPTIES_PATTERN = re.compile(r"\s\s+")
SINGLE_CHARACTER_PATTERN = re.compile(r"\b.\b")
PUNCTUATION_PATTERN = re.compile(r"[.:;!?,/\"\']")


def build_searchable_text(title: str, transcript: str) -> str:
    if not transcript:
        return title.lower()

    transcript_text = unescape(unescape(transcript))

    transcript_text = SQUARE_BRACKETS_PATTERN.sub(repl="\n", string=transcript_text)
    transcript_text = HTML_TAG_PATTERN.sub(repl="\n", string=transcript_text)
    transcript_text = SPEAKER_PATTERN.sub(repl="\n", string=transcript_text)
    transcript_text = SEPARATE_NUMBER_PATTERN.sub(repl=" ", string=transcript_text)
    transcript_text = PUNCTUATION_PATTERN.sub(repl=" ", string=transcript_text)

    normalized = "".join(ch for ch in transcript_text if ch.isalnum() or ch == " ")

    normalized = SINGLE_CHARACTER_PATTERN.sub(repl=" ", string=normalized)
    normalized = REPEATED_EMPTIES_PATTERN.sub(repl=" ", string=normalized)

    return (title.lower() + " :: " + normalized.strip().lower())[:3800]


T = TypeVar("T")


def cast_or_none(cast_to: type["T"], value: Any) -> T | None:
    if value:
        return cast_to(value)  # type: ignore[call-arg]
    return None


def slugify(
    string: str,
    replacements: tuple[tuple[str, str], ...] = (),
    separator: str = "-",
) -> str:
    return base_slugify(string, separator=separator, replacements=replacements)
