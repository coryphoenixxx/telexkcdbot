import re
from html import unescape

SQUARE_BRACKETS_PATTERN = re.compile(r"\[.*?]")
HTML_TAG_PATTERN = re.compile(r"<.*?>")
SPEAKER_PATTERN = re.compile(r"^[\[\w -\]]{3,20}: ", re.UNICODE | re.MULTILINE)
SEPARATE_NUMBER_PATTERN = re.compile(r"\s[0-9]+\s")
REPEATED_EMPTIES_PATTERN = re.compile(r"\s\s+")
SINGLE_CHARACTER_PATTERN = re.compile(r"\b.\b")
PUNCTUATION_PATTERN = re.compile(r"[.:;!?,/\"\']")


def build_searchable_text(title: str, raw_transcript: str, *, is_draft: bool = False) -> str:
    if is_draft:
        return ""

    transcript_text = unescape(unescape(raw_transcript))

    transcript_text = SQUARE_BRACKETS_PATTERN.sub(repl="\n", string=transcript_text)
    transcript_text = HTML_TAG_PATTERN.sub(repl="\n", string=transcript_text)
    transcript_text = SPEAKER_PATTERN.sub(repl="\n", string=transcript_text)
    transcript_text = SEPARATE_NUMBER_PATTERN.sub(repl=" ", string=transcript_text)
    transcript_text = PUNCTUATION_PATTERN.sub(repl=" ", string=transcript_text)

    normalized = "".join(ch for ch in transcript_text if ch.isalnum() or ch == " ")

    normalized = SINGLE_CHARACTER_PATTERN.sub(repl=" ", string=normalized)
    normalized = REPEATED_EMPTIES_PATTERN.sub(repl=" ", string=normalized)

    return (title.lower() + " :: " + normalized.strip().lower())[:3800]
