import re

REMOVE_SQUARE_BRACKETS = re.compile(r"\[.*?]")
REMOVE_TAGS = re.compile(r"<.*?>")
REMOVE_SPEAKERS = re.compile(r"^[\[\w -\]]{3,20}: ", re.UNICODE | re.MULTILINE)
REMOVE_REPEATED_EMPTIES = re.compile(r"(\s\s+)")


def build_searchable_text(title, transcript_raw: str) -> str:
    transcript_text = re.sub(pattern=REMOVE_SQUARE_BRACKETS, repl="\n", string=transcript_raw)
    transcript_text = re.sub(pattern=REMOVE_TAGS, repl="\n", string=transcript_text)
    transcript_text = re.sub(pattern=REMOVE_SPEAKERS, repl="\n", string=transcript_text)
    transcript_text = re.sub(pattern=REMOVE_REPEATED_EMPTIES, repl="\n", string=transcript_text)

    return (title + " " + transcript_text).strip()
