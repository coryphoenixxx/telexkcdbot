import re

SQUARE_BRACKETS_PATTERN = re.compile(r"\[.*?]")
HTML_TAG_PATTERN = re.compile(r"<.*?>")
SPEAKER_PATTERN = re.compile(r"^[\[\w -\]]{3,20}: ", re.UNICODE | re.MULTILINE)
PUNCTUATION_PATTERN = re.compile(r"[.:;!?,\"\']")
SEPARATE_NUMBER_PATTERN = re.compile(r"\s[0-9]+\s")
REPEATED_EMPTIES_PATTERN = re.compile(r"\s\s+")


def build_searchable_text(title, transcript_raw: str) -> str:
    transcript_text = SQUARE_BRACKETS_PATTERN.sub(repl="\n", string=transcript_raw)
    transcript_text = HTML_TAG_PATTERN.sub(repl="\n", string=transcript_text)
    transcript_text = SPEAKER_PATTERN.sub(repl="\n", string=transcript_text)
    transcript_text = PUNCTUATION_PATTERN.sub(repl=" ", string=transcript_text)
    transcript_text = SEPARATE_NUMBER_PATTERN.sub(repl=" ", string=transcript_text)
    transcript_text = REPEATED_EMPTIES_PATTERN.sub(repl=" ", string=transcript_text)
    transcript_text.replace('�', '')

    return (title + " :: " + transcript_text.strip().lower())[:4000]
