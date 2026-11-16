"""URL slugs from arbitrary titles."""

from __future__ import annotations

import re
import unicodedata


def slugify(title: str, max_length: int = 50) -> str:
    """Lowercase ASCII words joined by single hyphens, cut at a word boundary."""
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]", "-", text.lower()).strip("-")
    if len(text) <= max_length:
        return text
    cut = text[:max_length + 1].rfind("-")
    return text[:cut] if cut > 0 else text[:max_length]
