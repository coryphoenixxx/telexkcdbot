import re

SQUARE_BRACKETS_PATTERN = re.compile(r"\[.*?]")
HTML_TAG_PATTERN = re.compile(r"<.*?>")
SPEAKER_PATTERN = re.compile(r"^[\[\w -\]]{3,20}: ", re.UNICODE | re.MULTILINE)
PUNCTUATION_PATTERN = re.compile(r"[.:;!?,\"\']")
SEPARATE_NUMBER_PATTERN = re.compile(r"\s[0-9]+\s")
REPEATED_EMPTIES_PATTERN = re.compile(r"\s\s+")


def build_searchable_text(title, transcript_raw: str) -> str:
    transcript_text = re.sub(pattern=SQUARE_BRACKETS_PATTERN, repl="\n", string=transcript_raw)
    transcript_text = re.sub(pattern=HTML_TAG_PATTERN, repl="\n", string=transcript_text)
    transcript_text = re.sub(pattern=SPEAKER_PATTERN, repl="\n", string=transcript_text)
    transcript_text = re.sub(pattern=PUNCTUATION_PATTERN, repl=" ", string=transcript_text)
    transcript_text = re.sub(pattern=SEPARATE_NUMBER_PATTERN, repl=" ", string=transcript_text)
    transcript_text = re.sub(pattern=REPEATED_EMPTIES_PATTERN, repl=" ", string=transcript_text)
    transcript_text.replace('�', '')

    return (title + " :: " + transcript_text.strip().lower())[:4000]
