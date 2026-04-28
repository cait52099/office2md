import re


def clean_markdown(markdown: str) -> str:
    md = markdown.replace("\r\n", "\n").replace("\r", "\n")
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    md = re.sub(r"\n(#{1,6} )", r"\n\n\1", md)
    return md.strip() + "\n"

