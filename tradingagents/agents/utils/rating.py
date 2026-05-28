import re

RATINGS = ("Buy", "Overweight", "Hold", "Underweight", "Sell")

_RATINGS_PATTERN = "|".join(RATINGS)

# Pass 1 — explicit label: "Rating: Buy", "rating - Overweight", "**Rating: Hold**"
_LABEL_RE = re.compile(
    rf"(?:rating|recommendation)\s*[-:]\s*\*{{0,2}}({_RATINGS_PATTERN})\*{{0,2}}",
    re.IGNORECASE,
)
# Also catches inline bold: **Rating: Buy**
_BOLD_RE = re.compile(
    rf"\*\*\s*(?:rating|recommendation)\s*:\s*({_RATINGS_PATTERN})\s*\*\*",
    re.IGNORECASE,
)


def parse_rating(text: str, default: str = "Hold") -> str:
    """Heuristically extract a 5-tier rating from prose text.

    Pass 1: look for an explicit "Rating: X" label (tolerant of markdown bold).
    Pass 2: find the first occurrence of any rating word in the text.
    Pass 3: return default ("Hold") if nothing matched.
    """
    # Pass 1 — explicit label
    for pattern in (_LABEL_RE, _BOLD_RE):
        m = pattern.search(text)
        if m:
            return m.group(1).title()

    # Pass 2 — first rating word anywhere in the text
    for rating in RATINGS:
        if re.search(rf"\b{rating}\b", text, re.IGNORECASE):
            return rating  # already title-cased in RATINGS tuple

    return default