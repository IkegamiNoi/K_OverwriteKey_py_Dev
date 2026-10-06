"""Status text formatting shared by compact presentation components."""


def one_line(text: str) -> str:
    """Replace line breaks with spaces so text fits on one UI row."""
    return text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
