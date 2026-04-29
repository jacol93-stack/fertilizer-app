"""Server-side crop-name canonicaliser.

`crop_requirements.crop` is the source of truth for every downstream
catalog table — `crop_application_methods`, `perennial_age_factors`,
`fertilizer_rate_tables`, `crop_growth_stages`, `soil_sufficiency`,
etc. all `eq("crop", crop)` against the canonical Title-Case form
("Macadamia", "Citrus (Navel)", "Maize (dryland)").

Free-text user input — Excel cells, CSV imports, manual UI typing —
won't reliably match. This helper takes a user string and resolves it
to a canonical name (or raises an explicit ambiguity error so the
caller can prompt for a variant pick).

Resolution order:

  1. Exact match (already canonical) → return as-is.
  2. Case-insensitive exact match → return canonical capitalisation.
  3. Parent + variant disambiguation:
       - "citrus" → ambiguous (5 variants), unless `default_variant`
         is supplied.
       - "maize" → ambiguous (dryland / irrigated).
  4. Common-alias map (Afrikaans / shorthand / typo-tolerant):
       - "makadamia" → Macadamia
       - "sitrus" → Citrus (ambiguous follow-up)
       - "mac" / "macs" → Macadamia
       - "citrus navel" / "navel citrus" / "navel" → Citrus (Navel)
       - "valencia" / "valencias" → Citrus (Valencia)
       - "maize dryland" → Maize (dryland)
  5. No match → return input + warning, let downstream Pydantic
     validation surface "no methods configured for this crop" rather
     than guessing.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Optional


@dataclass(frozen=True)
class CanonicaliseResult:
    """Outcome of a single resolution attempt."""
    canonical: Optional[str]   # None when ambiguous and no default
    raw_input: str
    matched_via: str           # 'exact' | 'case_insensitive' | 'alias' | 'parent_default' | 'no_match' | 'ambiguous'
    warning: Optional[str] = None
    candidates: tuple[str, ...] = ()  # populated when ambiguous


# ============================================================
# Common SA crop aliases (Afrikaans + shorthand)
# ============================================================
#
# Keys are normalised — lowercase, single-spaced, no punctuation. The
# value is either a single canonical name or a tuple flagging an
# ambiguous parent that needs a variant pick.

_SINGLE_ALIASES: dict[str, str] = {
    # Macadamia
    "mac": "Macadamia",
    "macs": "Macadamia",
    "makadamia": "Macadamia",
    "macadamia nuts": "Macadamia",
    "noote": "Macadamia",  # generic Afrikaans for nuts
    # Pecan
    "pekanneut": "Pecan",
    "pecans": "Pecan",
    # Avocado
    "avocados": "Avocado",
    "avo": "Avocado",
    "avos": "Avocado",
    "advokaat": "Avocado",
    # Citrus variants (specific picks shouldn't trip the ambiguity check)
    "navel": "Citrus (Navel)",
    "navel citrus": "Citrus (Navel)",
    "navels": "Citrus (Navel)",
    "valencia": "Citrus (Valencia)",
    "valencias": "Citrus (Valencia)",
    "lemon": "Citrus (Lemon)",
    "lemons": "Citrus (Lemon)",
    "suurlemoen": "Citrus (Lemon)",
    "grapefruit": "Citrus (Grapefruit)",
    "soft citrus": "Citrus (Soft Citrus)",
    "mandarin": "Citrus (Soft Citrus)",
    "mandarins": "Citrus (Soft Citrus)",
    # Maize variants
    "maize dryland": "Maize (dryland)",
    "dryland maize": "Maize (dryland)",
    "maize irrigated": "Maize (irrigated)",
    "irrigated maize": "Maize (irrigated)",
    # Wheat / barley don't have variants — straight pass-through
    "koring": "Wheat",
    "gars": "Barley",
    "sojabone": "Soybean",
    "sojaboon": "Soybean",
    "grondboon": "Groundnut",
    "grondbone": "Groundnut",
    "grape": "Wine Grape",  # safer default — table grape needs explicit naming
    "grapes": "Wine Grape",
    "druiwe": "Wine Grape",
    # Vegetables
    "knoffel": "Garlic",
    "ui": "Onion",
    "uie": "Onion",
    "kool": "Cabbage",
    "wortel": "Carrot",
    "wortels": "Carrot",
    "aartappel": "Potato",
    "aartappels": "Potato",
    # Sugarcane
    "suikerriet": "Sugarcane",
    "cane": "Sugarcane",
    # Tea / coffee / tobacco
    "tee": "Tea",
    "koffie": "Coffee",
    "tabak": "Tobacco",
}

# Parent terms that need a variant pick. The value is the family name
# we report back so the caller can list the variants for the user.
_AMBIGUOUS_PARENTS: dict[str, str] = {
    "citrus": "Citrus",
    "sitrus": "Citrus",
    "citrus fruit": "Citrus",
    "maize": "Maize",
    "mielies": "Maize",
    "corn": "Maize",
}


def _normalise(s: str) -> str:
    """Lowercase, collapse whitespace, strip surrounding punctuation."""
    if not s:
        return ""
    return " ".join(s.lower().strip().split())


def canonicalise_crop(
    raw: str,
    *,
    catalog_crops: Iterable[str],
    default_variant: Optional[str] = None,
) -> CanonicaliseResult:
    """Resolve a user-supplied crop name to the canonical form.

    `catalog_crops` is the list of crop names from
    crop_requirements.crop — caller fetches once per request and
    passes through. We don't hit the DB from here.

    `default_variant` lets the caller pick a default for ambiguous
    parents (e.g. when bulk-importing a citrus farm where the agent
    has confirmed all blocks are Navel, pass `default_variant="Citrus
    (Navel)"`). Without it, ambiguous inputs return canonical=None
    plus the variant list.
    """
    raw_input = (raw or "").strip()
    if not raw_input:
        return CanonicaliseResult(
            canonical=None,
            raw_input=raw_input,
            matched_via="no_match",
            warning="Crop is empty.",
        )

    catalog_set = list(catalog_crops or [])
    canonical_set = set(catalog_set)
    lower_to_canonical: dict[str, str] = {c.lower(): c for c in catalog_set}

    # 1. Exact match — already canonical
    if raw_input in canonical_set:
        return CanonicaliseResult(
            canonical=raw_input, raw_input=raw_input, matched_via="exact",
        )

    norm = _normalise(raw_input)

    # 2. Case-insensitive exact match
    if norm in lower_to_canonical:
        return CanonicaliseResult(
            canonical=lower_to_canonical[norm],
            raw_input=raw_input,
            matched_via="case_insensitive",
        )

    # 3. Alias map — single-canonical aliases
    if norm in _SINGLE_ALIASES:
        canonical = _SINGLE_ALIASES[norm]
        if canonical in canonical_set:
            return CanonicaliseResult(
                canonical=canonical,
                raw_input=raw_input,
                matched_via="alias",
            )

    # 4. Ambiguous parent — list variants, optionally pick default
    if norm in _AMBIGUOUS_PARENTS:
        family = _AMBIGUOUS_PARENTS[norm]
        variants = sorted(
            c for c in catalog_set
            if c.startswith(f"{family} (") or c == family
        )
        # If `default_variant` was supplied AND it's a real variant of
        # this family, take it. Otherwise raise ambiguity.
        if default_variant and default_variant in variants:
            return CanonicaliseResult(
                canonical=default_variant,
                raw_input=raw_input,
                matched_via="parent_default",
                warning=(
                    f"'{raw_input}' is a parent term — defaulted to "
                    f"'{default_variant}'. Other variants: {', '.join(v for v in variants if v != default_variant)}."
                ),
            )
        return CanonicaliseResult(
            canonical=None,
            raw_input=raw_input,
            matched_via="ambiguous",
            candidates=tuple(variants),
            warning=(
                f"'{raw_input}' could be any of {len(variants)} {family} "
                f"variants ({', '.join(variants)}). Pick one explicitly."
            ),
        )

    # 5. No match — return as-is with warning. We don't hard-fail here
    # because the caller may want to surface the row in a preview and
    # let the agronomist decide; downstream catalog joins will silently
    # return no methods / no targets for the unknown crop.
    return CanonicaliseResult(
        canonical=None,
        raw_input=raw_input,
        matched_via="no_match",
        warning=(
            f"'{raw_input}' didn't match any canonical crop name. "
            f"Check spelling or pick from the catalog."
        ),
    )


@lru_cache(maxsize=1)
def _ascii_fold(s: str) -> str:
    """Diacritic-insensitive comparison — kept tiny because we only
    need it for the few SA crop names with accents (none today, but
    future Mediterranean / vlei specialty names may have them)."""
    out = []
    for ch in s:
        if ch in ("é", "è", "ê", "ë"):
            out.append("e")
        elif ch in ("á", "à", "â", "ä"):
            out.append("a")
        elif ch in ("í", "ì", "î", "ï"):
            out.append("i")
        elif ch in ("ó", "ò", "ô", "ö"):
            out.append("o")
        elif ch in ("ú", "ù", "û", "ü"):
            out.append("u")
        else:
            out.append(ch)
    return "".join(out)
