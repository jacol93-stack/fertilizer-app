"""Single source of truth for soil-value canonicalisation.

Every soil-data ingestion path — AI extractor, bulk xlsx, manual form,
direct API POST — flows through `canonicalise_soil_values`. The engine
then reads ONLY canonical form: same keys (matching `soil_sufficiency.
parameter`), same units per key, magnitude validated. This module is
the boundary; the engine should never need to second-guess what unit
something arrived in.

Why this exists: through 2026-04 the system accumulated a series of
unit-confusion bugs — Na (mg/kg) divided by CEC (cmol/kg), classifier
missing K because the lab labelled it `K (mg/kg)` not `K`, ESP rendered
as 374 % because two different unit conventions collided. Each was
patched at the consumer; this module makes the patching unnecessary.

Design rules:

    1. Canonical key set MATCHES `soil_sufficiency.parameter` so the
       classifier's lookups work without translation. That means
       `K`, `Ca`, `Mg`, `Na`, `S`, `pH (KCl)`, `P (Bray-1)`, etc.
       (parens are a method qualifier, not a unit, so they stay).

    2. Each canonical key declares ONE canonical unit. All conversions
       happen on the way IN. The engine then reads canonical-unit
       values and may convert internally for math (e.g. cmol/kg for
       cation-ratio calc) but never has to handle ambiguity from the
       caller.

    3. Plausible-magnitude range per parameter. Catches both data
       errors ("K=2.0" submitted as cmol/kg when the engine expects
       mg/kg → way below plausible range → flagged) and
       transcription errors ("100" entered as 100 cmol when 100 mg/kg
       was meant).

    4. Unknown keys are passed through as-is rather than dropped, so
       custom lab parameters survive without config changes. They
       just don't get classified or converted.

    5. Output carries provenance so the audit trail can answer "where
       did this value come from?". Stored alongside in `raw_values`
       on the row.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Canonical schema ────────────────────────────────────────────────


@dataclass(frozen=True)
class ParamSpec:
    """Specification for one canonical soil parameter."""
    canonical_unit: str
    """Single unit every consumer reads. e.g. 'mg/kg' for K."""
    aliases: tuple[str, ...]
    """Other lab-header forms that map to this canonical key. Match is
    case-insensitive after stripping a trailing unit-bearing parens
    group. Order matters only for diagnostics — first hit wins."""
    accepted_units: dict[str, float]
    """Unit → multiplier-to-canonical-unit. Multiplier = factor that
    converts a raw value in this unit to the canonical unit. So if
    canonical is mg/kg and the raw was cmol_c/kg, multiplier is the
    equivalent weight (e.g. 391.0 for K). 1.0 means no conversion."""
    plausible_range: tuple[float, float]
    """(min, max) the canonical-unit value must fall inside. Outside
    this band gets a 'magnitude_warning' diagnostic — usually a
    transcription error or a unit mismatch we couldn't catch via the
    label alone."""
    category: str
    """Display / engine grouping. One of: 'cation_absolute',
    'anion_absolute', 'micro', 'saturation', 'ratio', 'pH', 'physical',
    'organic', 'cec', 'macro_anion'."""


# Cation equivalent weights — 1 cmol_c/kg of the ion equals this many mg/kg.
# Atomic mass / charge × 10 (the cmol → mol factor). Mirrors
# CATION_EQUIVALENT_WEIGHT_MG_PER_CMOL in soil_engine.py.
_K_EQ = 391.0
_CA_EQ = 200.4
_MG_EQ = 121.56
_NA_EQ = 229.9


# Canonical registry. Keys MUST exactly match `soil_sufficiency.parameter`
# values where a sufficiency row exists, so classify_soil_value works
# directly without further translation.
CANONICAL_PARAMETERS: dict[str, ParamSpec] = {
    # ── pH ───────────────────────────────────────────────────────────
    "pH (KCl)": ParamSpec(
        canonical_unit="pH",
        aliases=("pH (KCl)", "pH KCl", "pH_KCl", "pH-KCl"),
        accepted_units={"pH": 1.0, "": 1.0},
        plausible_range=(2.5, 10.0),
        category="pH",
    ),
    "pH (H2O)": ParamSpec(
        canonical_unit="pH",
        aliases=("pH (H2O)", "pH H2O", "pH_H2O", "pH-H2O", "pH (water)", "pH water"),
        accepted_units={"pH": 1.0, "": 1.0},
        plausible_range=(2.5, 10.0),
        category="pH",
    ),

    # ── Cations (mg/kg canonical — matches existing engine assumption) ─
    "K": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("K", "Potassium", "Exchangeable K", "K exch", "K (exchangeable)"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0, "cmol_c/kg": _K_EQ, "cmol/kg": _K_EQ, "meq/100g": _K_EQ},
        plausible_range=(1.0, 5000.0),
        category="cation_absolute",
    ),
    "Ca": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("Ca", "Calcium", "Exchangeable Ca", "Ca exch", "Ca (exchangeable)"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0, "cmol_c/kg": _CA_EQ, "cmol/kg": _CA_EQ, "meq/100g": _CA_EQ},
        plausible_range=(10.0, 20000.0),
        category="cation_absolute",
    ),
    "Mg": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("Mg", "Magnesium", "Exchangeable Mg", "Mg exch", "Mg (exchangeable)"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0, "cmol_c/kg": _MG_EQ, "cmol/kg": _MG_EQ, "meq/100g": _MG_EQ},
        plausible_range=(1.0, 5000.0),
        category="cation_absolute",
    ),
    "Na": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("Na", "Sodium", "Exchangeable Na", "Na exch", "Na (exchangeable)"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0, "cmol_c/kg": _NA_EQ, "cmol/kg": _NA_EQ, "meq/100g": _NA_EQ},
        plausible_range=(0.1, 5000.0),
        category="cation_absolute",
    ),

    # ── CEC ──────────────────────────────────────────────────────────
    "CEC": ParamSpec(
        canonical_unit="cmol_c/kg",
        aliases=("CEC", "T Value", "T-value", "T-Value", "CEC (cmol/kg)", "CEC cmol/kg",
                 "S-Value", "S Value"),  # S-Value = sum of bases ≈ CEC for non-acidic soils
        accepted_units={"cmol_c/kg": 1.0, "cmol/kg": 1.0, "meq/100g": 1.0},
        plausible_range=(0.5, 80.0),
        category="cec",
    ),
    "Exchangeable Acid": ParamSpec(
        canonical_unit="cmol_c/kg",
        aliases=("Exchangeable Acid", "Exch Acid", "H+Al"),
        accepted_units={"cmol_c/kg": 1.0, "cmol/kg": 1.0, "meq/100g": 1.0},
        plausible_range=(0.0, 20.0),
        category="cec",
    ),

    # ── Saturations (% of CEC) ───────────────────────────────────────
    "K Saturation": ParamSpec(
        canonical_unit="%",
        aliases=("K Saturation", "K base sat", "K_base_sat_pct", "K base sat %"),
        accepted_units={"%": 1.0, "fraction": 100.0},
        plausible_range=(0.0, 100.0),
        category="saturation",
    ),
    "Ca Saturation": ParamSpec(
        canonical_unit="%",
        aliases=("Ca Saturation", "Ca base sat", "Ca_base_sat_pct", "Ca base sat %"),
        accepted_units={"%": 1.0, "fraction": 100.0},
        plausible_range=(0.0, 100.0),
        category="saturation",
    ),
    "Mg Saturation": ParamSpec(
        canonical_unit="%",
        aliases=("Mg Saturation", "Mg base sat", "Mg_base_sat_pct", "Mg base sat %"),
        accepted_units={"%": 1.0, "fraction": 100.0},
        plausible_range=(0.0, 100.0),
        category="saturation",
    ),
    "Na Saturation": ParamSpec(
        canonical_unit="%",
        aliases=("Na Saturation", "Na base sat", "Na_base_sat_pct", "Na base sat %",
                 "ESP", "Exchangeable Sodium Percentage"),
        accepted_units={"%": 1.0, "fraction": 100.0},
        plausible_range=(0.0, 100.0),
        category="saturation",
    ),
    "Acid Saturation": ParamSpec(
        canonical_unit="%",
        aliases=("Acid Saturation", "Acid sat", "Al saturation", "Al sat",
                 "Al_saturation_pct"),
        accepted_units={"%": 1.0, "fraction": 100.0},
        plausible_range=(0.0, 100.0),
        category="saturation",
    ),

    # ── Phosphorus (multiple methods, NOT interchangeable) ───────────
    "P (Bray-1)": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("P (Bray-1)", "P Bray-1", "P_Bray1", "P Bray 1", "Bray-1 P", "Bray P"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0, "mg/L": 1.0},  # mg/L for FAS volumetric
        plausible_range=(1.0, 500.0),
        category="anion_absolute",
    ),
    "P (Citric acid)": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("P (Citric acid)", "P Citric", "P_Citric", "Citric acid P"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0},
        plausible_range=(1.0, 500.0),
        category="anion_absolute",
    ),
    "P (Olsen)": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("P (Olsen)", "P Olsen", "Olsen P"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0},
        plausible_range=(1.0, 200.0),
        category="anion_absolute",
    ),

    # ── Sulphur + macro-N ────────────────────────────────────────────
    "S": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("S", "Sulphur", "Sulfur", "Sulphate-S", "SO4-S"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0},
        plausible_range=(0.5, 500.0),
        category="anion_absolute",
    ),
    "N (total)": ParamSpec(
        canonical_unit="%",
        aliases=("N (total)", "N total", "Total N", "TN"),
        accepted_units={"%": 1.0, "fraction": 100.0, "mg/kg": 0.0001, "ppm": 0.0001},
        plausible_range=(0.001, 5.0),
        category="organic",
    ),

    # ── Micros (mg/kg) ───────────────────────────────────────────────
    "B": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("B", "Boron", "Hot water B", "B (HWS)"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0},
        plausible_range=(0.05, 20.0),
        category="micro",
    ),
    "Zn": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("Zn", "Zinc", "DTPA Zn"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0},
        plausible_range=(0.05, 200.0),
        category="micro",
    ),
    "Fe": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("Fe", "Iron", "DTPA Fe"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0},
        plausible_range=(0.5, 1000.0),
        category="micro",
    ),
    "Mn": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("Mn", "Manganese", "DTPA Mn"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0},
        plausible_range=(0.1, 500.0),
        category="micro",
    ),
    "Cu": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("Cu", "Copper", "DTPA Cu"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0},
        plausible_range=(0.05, 200.0),
        category="micro",
    ),
    "Mo": ParamSpec(
        canonical_unit="mg/kg",
        aliases=("Mo", "Molybdenum"),
        accepted_units={"mg/kg": 1.0, "ppm": 1.0},
        plausible_range=(0.01, 20.0),
        category="micro",
    ),

    # ── Organic + physical ───────────────────────────────────────────
    "Org C": ParamSpec(
        canonical_unit="%",
        aliases=("Org C", "OC", "Organic C", "Organic Carbon", "C (%)", "C", "Walkley-Black"),
        accepted_units={"%": 1.0, "fraction": 100.0, "g/kg": 0.1},
        plausible_range=(0.05, 15.0),
        category="organic",
    ),
    "Org M": ParamSpec(
        # Organic matter — converted to Org C via Van Bemmelen (× 1/1.724)
        # but kept as a separate canonical key since labs report it.
        canonical_unit="%",
        aliases=("Org M", "OM", "Organic M", "Organic Matter"),
        accepted_units={"%": 1.0, "fraction": 100.0, "g/kg": 0.1},
        plausible_range=(0.1, 25.0),
        category="organic",
    ),
    "Clay": ParamSpec(
        canonical_unit="%",
        aliases=("Clay", "Clay %", "Clay (%)", "Clay content"),
        accepted_units={"%": 1.0, "fraction": 100.0},
        plausible_range=(0.0, 100.0),
        category="physical",
    ),
    "Bulk Density": ParamSpec(
        canonical_unit="g/cm3",
        aliases=("Bulk Density", "BD", "Bulk Density (g/ml)", "Bulk density"),
        accepted_units={"g/cm3": 1.0, "g/ml": 1.0, "g/cc": 1.0, "kg/L": 1.0, "kg/m3": 0.001},
        plausible_range=(0.5, 2.5),
        category="physical",
    ),
    "EC": ParamSpec(
        canonical_unit="dS/m",
        aliases=("EC", "Electrical Conductivity", "Salinity"),
        accepted_units={"dS/m": 1.0, "mS/cm": 1.0, "mS/m": 0.1, "uS/cm": 0.001},
        plausible_range=(0.01, 30.0),
        category="physical",
    ),

    # ── Ratios — labs sometimes pre-compute these. Stored as-is. ─────
    "Ca:Mg": ParamSpec(
        canonical_unit="ratio",
        aliases=("Ca:Mg", "Ca/Mg", "Ca to Mg"),
        accepted_units={"ratio": 1.0, "": 1.0},
        plausible_range=(0.1, 20.0),
        category="ratio",
    ),
    "Ca:K": ParamSpec(
        canonical_unit="ratio",
        aliases=("Ca:K", "Ca/K", "Ca to K"),
        accepted_units={"ratio": 1.0, "": 1.0},
        plausible_range=(0.1, 100.0),
        category="ratio",
    ),
    "Mg:K": ParamSpec(
        canonical_unit="ratio",
        aliases=("Mg:K", "Mg/K", "Mg to K"),
        accepted_units={"ratio": 1.0, "": 1.0},
        plausible_range=(0.1, 100.0),
        category="ratio",
    ),
    "Na:K": ParamSpec(
        canonical_unit="ratio",
        aliases=("Na:K", "Na/K", "Na to K"),
        accepted_units={"ratio": 1.0, "": 1.0},
        plausible_range=(0.0, 50.0),
        category="ratio",
    ),
    "(Ca+Mg):K": ParamSpec(
        canonical_unit="ratio",
        aliases=("(Ca+Mg):K", "(Ca+Mg)/K", "Ca+Mg : K", "(Ca+Mg) to K"),
        accepted_units={"ratio": 1.0, "": 1.0},
        plausible_range=(0.5, 200.0),
        category="ratio",
    ),
}


# Pre-computed reverse lookup: alias (case-folded) → canonical key.
def _build_alias_lookup() -> dict[str, str]:
    out: dict[str, str] = {}
    for canonical_key, spec in CANONICAL_PARAMETERS.items():
        for alias in spec.aliases:
            out[alias.casefold().strip()] = canonical_key
        # Always include the canonical key itself.
        out[canonical_key.casefold().strip()] = canonical_key
    return out


_ALIAS_LOOKUP = _build_alias_lookup()


# ── Output types ────────────────────────────────────────────────────


@dataclass
class ParamDiagnostic:
    """Per-parameter note — surfaced to the operator + audit log."""
    severity: str  # "info" | "warn" | "error"
    parameter: str  # canonical key (or original_label if no canonical match)
    original_label: str
    message: str


@dataclass
class CanonicalSoilValues:
    """Output of canonicalise_soil_values."""
    values: dict[str, float] = field(default_factory=dict)
    """canonical_key → value in canonical unit. The engine reads from here."""
    raw: dict[str, object] = field(default_factory=dict)
    """Verbatim copy of the input. Stored on the row for audit /
    reprocessing."""
    metadata: dict[str, dict] = field(default_factory=dict)
    """canonical_key → {original_label, original_unit, original_value,
    conversion_factor, magnitude_status}. Per-parameter provenance."""
    diagnostics: list[ParamDiagnostic] = field(default_factory=list)
    """Operator-facing notes — unknown parameters, magnitude warnings,
    unit fallbacks. Surfaced in the upload-review UI."""


# ── Helpers ─────────────────────────────────────────────────────────


_UNIT_SUFFIX_MAP: dict[str, str] = {
    # Lower-cased unit-bearing parens-content → canonical unit string.
    # Used to extract the unit from labels like "K (mg/kg)".
    "mg/kg": "mg/kg",
    "ppm": "ppm",
    "cmol_c/kg": "cmol_c/kg",
    "cmol/kg": "cmol/kg",
    "meq/100g": "meq/100g",
    "%": "%",
    "g/ml": "g/ml",
    "g/cm3": "g/cm3",
    "g/cc": "g/cc",
    "kg/l": "kg/L",
    "kg/m3": "kg/m3",
    "ds/m": "dS/m",
    "ms/cm": "mS/cm",
    "ms/m": "mS/m",
    "us/cm": "uS/cm",
    "g/kg": "g/kg",
    "mg/l": "mg/L",
    "fraction": "fraction",
    "ratio": "ratio",
    "ph": "pH",
}


def _split_label_and_unit(label: str) -> tuple[str, Optional[str]]:
    """Strip a trailing unit-bearing parens group from a column label.

    Returns (label_without_unit, unit_or_None).

    Lab labels look like "K (mg/kg)", "P (Bray-1) (mg/kg)" (two parens —
    method qualifier + unit), "pH (KCl)" (parens but content is method,
    not a unit), "Acid Saturation (%)" (% counts as unit). Heuristic:
    only treat the LAST trailing parens group as a unit if its content
    matches a known unit string from `_UNIT_SUFFIX_MAP`.
    """
    if not label:
        return label, None
    s = label.strip()
    if not s.endswith(")"):
        return s, None
    open_idx = s.rfind("(")
    if open_idx < 0:
        return s, None
    inside = s[open_idx + 1:-1].strip()
    inside_normalised = inside.casefold()
    if inside_normalised in _UNIT_SUFFIX_MAP:
        return s[:open_idx].strip(), _UNIT_SUFFIX_MAP[inside_normalised]
    return s, None


def _resolve_canonical(label_no_unit: str) -> Optional[str]:
    """Map a unit-stripped label to its canonical key, if any."""
    if not label_no_unit:
        return None
    return _ALIAS_LOOKUP.get(label_no_unit.casefold().strip())


def _coerce_numeric(value: object) -> Optional[float]:
    """Convert a raw value to float. Tolerates strings with stray
    spaces, commas (European decimals), and leading symbols ('<', '>').
    Returns None if the value can't be coerced."""
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    # Strip detection-limit prefixes ('< 5', '> 100')
    if s[0] in "<>":
        s = s[1:].strip()
    # European decimals: "1,3" → "1.3" only when there's no other dot
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    # Strip non-numeric trailing chars (e.g. "5.4 mg/kg" stuck together)
    end = len(s)
    for i, ch in enumerate(s):
        if ch in "0123456789.-+eE":
            continue
        end = i
        break
    s = s[:end]
    try:
        return float(s) if s else None
    except (TypeError, ValueError):
        return None


# ── Main entry point ────────────────────────────────────────────────


def canonicalise_soil_values(
    raw: dict[str, object],
    source: str = "unknown",
    explicit_units: Optional[dict[str, str]] = None,
) -> CanonicalSoilValues:
    """Convert a raw lab/manual/AI-extracted soil-values dict to canonical
    form.

    Args:
        raw: dict of {label: value} as received from the source. Labels
            may carry unit suffixes ("K (mg/kg)") or be canonical
            ("K"). Values may be numeric or numeric-ish strings.
        source: provenance tag — "lab_pdf", "lab_xlsx", "ai_extractor",
            "manual_form", "api_direct". Logged in metadata.
        explicit_units: optional override dict {label: unit}. The
            manual-entry form sends this when the user picked a unit
            from a dropdown — that takes priority over any unit parsed
            from the label itself.

    Returns:
        CanonicalSoilValues with canonical-unit values, raw copy, per-
        parameter metadata, and diagnostics for operator review.
    """
    explicit_units = explicit_units or {}
    out = CanonicalSoilValues()
    out.raw = dict(raw)

    # Track canonical keys we've already populated so we can warn on
    # duplicate inputs (e.g. lab gives both "K" and "K (mg/kg)").
    seen_canonical: set[str] = set()

    for label, raw_value in raw.items():
        if raw_value is None or raw_value == "":
            continue

        numeric = _coerce_numeric(raw_value)
        if numeric is None:
            out.diagnostics.append(ParamDiagnostic(
                severity="warn",
                parameter=str(label),
                original_label=str(label),
                message=f"Couldn't parse value '{raw_value}' as a number — dropped.",
            ))
            continue

        # Determine canonical key + unit.
        label_no_unit, parsed_unit = _split_label_and_unit(str(label))
        canonical_key = _resolve_canonical(label_no_unit)

        if canonical_key is None:
            # Unknown parameter — pass through under its original label
            # so custom lab columns survive without config changes.
            # Engine code that doesn't care will just not use it.
            out.values[str(label)] = numeric
            out.metadata[str(label)] = {
                "original_label": str(label),
                "original_unit": parsed_unit or explicit_units.get(str(label)),
                "original_value": raw_value,
                "canonical": False,
            }
            out.diagnostics.append(ParamDiagnostic(
                severity="info",
                parameter=str(label),
                original_label=str(label),
                message=f"Unknown parameter '{label}' — preserved as-is, not classified.",
            ))
            continue

        spec = CANONICAL_PARAMETERS[canonical_key]

        # Resolve the unit. Priority: explicit_units (from the manual
        # form) > parsed unit from label > canonical default.
        unit = explicit_units.get(str(label)) or parsed_unit or spec.canonical_unit

        # Normalise unit string for the lookup (case-fold, kill spaces).
        unit_key = unit
        if unit_key not in spec.accepted_units:
            # Try a case-insensitive match.
            for accepted in spec.accepted_units:
                if accepted.casefold() == str(unit).casefold():
                    unit_key = accepted
                    break
            else:
                # Unit not recognised for this parameter. Fall back to
                # canonical, but flag for review.
                out.diagnostics.append(ParamDiagnostic(
                    severity="warn",
                    parameter=canonical_key,
                    original_label=str(label),
                    message=(
                        f"Unit '{unit}' not recognised for {canonical_key}; "
                        f"assuming canonical {spec.canonical_unit}. "
                        f"Verify in the source document."
                    ),
                ))
                unit_key = spec.canonical_unit

        multiplier = spec.accepted_units.get(unit_key, 1.0)
        canonical_value = numeric * multiplier

        # Magnitude validation.
        lo, hi = spec.plausible_range
        magnitude_status = "ok"
        if canonical_value < lo or canonical_value > hi:
            magnitude_status = "out_of_range"
            out.diagnostics.append(ParamDiagnostic(
                severity="warn",
                parameter=canonical_key,
                original_label=str(label),
                message=(
                    f"{canonical_key} = {canonical_value:.3g} {spec.canonical_unit} is "
                    f"outside the plausible range "
                    f"[{lo}, {hi}] {spec.canonical_unit}. "
                    f"Likely a unit mismatch or transcription error — verify in the source."
                ),
            ))

        if canonical_key in seen_canonical:
            # Multiple input rows resolve to the same canonical key.
            # Keep the first (deterministic) and flag the second.
            out.diagnostics.append(ParamDiagnostic(
                severity="info",
                parameter=canonical_key,
                original_label=str(label),
                message=(
                    f"Duplicate input for {canonical_key} — "
                    f"keeping first; '{label}' ignored."
                ),
            ))
            continue

        out.values[canonical_key] = canonical_value
        out.metadata[canonical_key] = {
            "original_label": str(label),
            "original_unit": unit_key,
            "original_value": raw_value,
            "conversion_factor": multiplier,
            "magnitude_status": magnitude_status,
            "source": source,
            "canonical": True,
        }
        seen_canonical.add(canonical_key)

    # Special-case: derive Org C from Org M when only Org M was provided.
    # Van Bemmelen factor — OC = OM / 1.724.
    if "Org C" not in out.values and "Org M" in out.values:
        oc = out.values["Org M"] / 1.724
        out.values["Org C"] = round(oc, 3)
        out.metadata["Org C"] = {
            "original_label": "Org M",
            "original_unit": "%",
            "original_value": out.values["Org M"],
            "conversion_factor": 1.0 / 1.724,
            "magnitude_status": "derived",
            "source": "derived_from_Org_M",
            "canonical": True,
        }

    return out


# ── Convenience helpers for callers ─────────────────────────────────


def canonicalise_parameter_name(name: str) -> str:
    """Resolve a parameter label (lab-data key, sufficiency-row name,
    override-row name) to its canonical form. Returns the input verbatim
    when no alias matches — so unknown columns survive without dropping.

    Used by the merging code in `soil_engine.merge_sufficiency_for_crop`
    to make sure rows keyed `'K'`, `'K (exchangeable)'`, `'Exchangeable K'`,
    `'Potassium'` collapse into the same canonical entry instead of
    fragmenting and silently disabling crop overrides.
    """
    if not name:
        return name
    label_no_unit, _ = _split_label_and_unit(str(name))
    canonical = _resolve_canonical(label_no_unit)
    return canonical if canonical else str(name)


def list_canonical_parameters() -> list[dict]:
    """Return a UI-friendly list of every canonical parameter with its
    accepted units and category. Used by the manual-entry form to
    populate parameter + unit dropdowns."""
    out: list[dict] = []
    for key, spec in CANONICAL_PARAMETERS.items():
        out.append({
            "canonical_key": key,
            "canonical_unit": spec.canonical_unit,
            "category": spec.category,
            "accepted_units": list(spec.accepted_units.keys()),
            "plausible_range": list(spec.plausible_range),
        })
    return out
