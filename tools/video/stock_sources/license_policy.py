"""Conservative commercial-use screen for stock-media licence metadata.

This is a first-pass allowlist, not legal advice or a replacement for
checking the individual asset's source page and current terms.
"""
from __future__ import annotations

import re


_RESTRICTED_MARKERS = (
    "noncommercial",
    "non-commercial",
    "no derivatives",
    "no known copyright restrictions",
    "no known rights",
    "no-derivatives",
    "cc by-nc",
    "cc-by-nc",
    "cc by-nd",
    "cc-by-nd",
    "rights vary",
    "verify per-file",
    "verify each",
    "with caveats",
    "caveat",
    "unknown",
    "all rights reserved",
)


def is_commercially_usable_license(
    license_text: str,
    *,
    creator: str = "",
    source_url: str = "",
) -> bool:
    """Return True only for explicit PD/CC0/CC BY/CC BY-SA metadata.

    CC BY and CC BY-SA candidates must carry both creator attribution and
    a human-readable source page. NC, ND, ambiguous, missing, and caveated
    licence strings are rejected.
    """
    raw = str(license_text or "").strip()
    if not raw:
        return False

    value = re.sub(r"\s+", " ", raw.lower()).strip()
    if any(marker in value for marker in _RESTRICTED_MARKERS):
        return False

    if "public domain" in value or "cc0" in value or "/publicdomain/" in value:
        return bool(source_url.strip()) if source_url else True

    cc_by = bool(
        re.search(r"\bcc\s*[- ]?by(?:\s*[- ]?sa)?(?:\b|/)", value)
        or re.search(r"creativecommons\.org/licenses/by(?:-sa)?/", value)
        or "creative commons attribution" in value
    )
    if not cc_by:
        return False

    # Attribution is mandatory for CC BY and CC BY-SA.
    return bool(creator.strip() and source_url.strip())
