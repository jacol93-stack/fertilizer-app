"""Extract soil analysis values from lab report PDFs/photos using Claude vision."""

import base64
import json
from typing import Any

import anthropic

from app.config import get_settings
from app.supabase_client import get_supabase_admin

# Soil parameters we expect from lab reports
EXPECTED_PARAMS = [
    "pH (KCl)", "pH (H2O)", "Resistance (Ohm)", "Organic C (%)",
    "Total N (%)", "NH4-N (mg/kg)", "NO3-N (mg/kg)",
    "P (Bray-1) (mg/kg)", "P (Bray-2) (mg/kg)", "P (Olsen) (mg/kg)",
    "K (mg/kg)", "Ca (mg/kg)", "Mg (mg/kg)", "Na (mg/kg)",
    "S (mg/kg)", "Mn (mg/kg)", "Fe (mg/kg)", "Cu (mg/kg)",
    "Zn (mg/kg)", "B (mg/kg)", "Mo (mg/kg)",
    "CEC (cmol/kg)", "Clay (%)",
    "Ca Saturation (%)", "Mg Saturation (%)", "K Saturation (%)",
    "Na Saturation (%)", "Acid Saturation (%)",
]


def _build_extraction_prompt(lab_template: dict | None = None) -> str:
    """Build the system prompt for Claude to extract soil values."""
    base = (
        "You are a soil/leaf lab report data extractor. Extract ALL analysis values "
        "from this lab report image/PDF.\n\n"
        "IMPORTANT: The report may contain MULTIPLE samples (rows in a table). "
        "Each row is a separate sample/block with its own values.\n\n"
        "Return a JSON object with these keys:\n"
        '- "lab_name": the laboratory name (string)\n'
        '- "report_number": report/certificate number if visible (string or null)\n'
        '- "analysis_date": date of analysis if visible (string or null)\n'
        '- "client": client name if visible (string or null)\n'
        '- "department": e.g. "Soil", "Leaf", "Water" (string or null)\n'
        '- "samples": array of sample objects, one per row/sample in the report\n\n'
        "Each sample object must have:\n"
        '- "sample_id": lab sample number (string)\n'
        '- "block_name": block/field identifier if visible (string or null)\n'
        '- "crop": fruit/crop type if visible (string or null)\n'
        '- "cultivar": cultivar/variety if visible (string or null)\n'
        '- "values": object mapping parameter names to numeric values\n\n'
        "If there is only ONE sample, still return it as a single-element array.\n\n"
        "For the values object, use these standard parameter names where possible:\n"
    )
    for p in EXPECTED_PARAMS:
        base += f"  - {p}\n"

    base += (
        "\nRules:\n"
        "- Extract EVERY row/sample in the table — do not skip any\n"
        "- Values must be numeric (no units in the value, just the number)\n"
        "- If a value is given as a range, use the midpoint\n"
        "- If a value shows '<' (below detection), use 0\n"
        "- Map lab-specific parameter names to the standard names above\n"
        "- For leaf analyses: N, P, K, Ca, Mg are typically in %, micros in mg/kg\n"
        "- Include norms/reference rows if present (mark them with block_name: 'Norm - Low', 'Norm - High' etc.)\n"
        "- Return ONLY valid JSON, no markdown or explanation\n"
    )

    if lab_template and lab_template.get("field_mappings"):
        base += (
            "\nThis lab report is from a known lab. Use these field mappings "
            "to improve accuracy:\n"
        )
        for lab_field, our_field in lab_template["field_mappings"].items():
            base += f'  - "{lab_field}" → "{our_field}"\n'

    return base


def extract_from_document(
    file_bytes: bytes,
    content_type: str,
    lab_name_hint: str | None = None,
) -> dict[str, Any]:
    """Extract soil analysis values from a lab report PDF or image.

    Returns dict with keys: lab_name, analysis_date, sample_id, values, confidence
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Check for existing lab template
    lab_template = None
    if lab_name_hint:
        lab_template = _get_lab_template(lab_name_hint)

    prompt = _build_extraction_prompt(lab_template)

    # Build the message content based on file type
    if content_type == "application/pdf":
        media_type = "application/pdf"
        source_type = "base64"
        source_key = "data"
    elif content_type in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        media_type = content_type
        source_type = "base64"
        source_key = "data"
    else:
        raise ValueError(f"Unsupported file type: {content_type}")

    b64_data = base64.standard_b64encode(file_bytes).decode("utf-8")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document" if content_type == "application/pdf" else "image",
                        "source": {
                            "type": source_type,
                            "media_type": media_type,
                            source_key: b64_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
    )

    # Track usage
    input_tokens = message.usage.input_tokens if message.usage else 0
    output_tokens = message.usage.output_tokens if message.usage else 0
    # Sonnet pricing: $3/M input, $15/M output
    cost_usd = round((input_tokens * 3 + output_tokens * 15) / 1_000_000, 6)

    # Parse the response
    response_text = message.content[0].text.strip()
    # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
    if response_text.startswith("```"):
        # Remove opening fence line (```json or ```)
        first_newline = response_text.find("\n")
        if first_newline > 0:
            response_text = response_text[first_newline + 1:]
        else:
            response_text = response_text[3:]
        # Remove closing fence
        if response_text.rstrip().endswith("```"):
            response_text = response_text.rstrip()[:-3].rstrip()

    try:
        extracted = json.loads(response_text)
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse extraction result from AI: {response_text[:200]}")

    # If we got a lab name, try to find/create template
    detected_lab = extracted.get("lab_name", "")
    if detected_lab and not lab_template:
        lab_template = _get_lab_template(detected_lab)

    # Handle both multi-sample and single-sample responses
    samples = extracted.get("samples", [])
    if not samples and extracted.get("values"):
        # Old single-sample format — wrap it
        samples = [{
            "sample_id": extracted.get("sample_id"),
            "block_name": None,
            "crop": None,
            "cultivar": None,
            "values": extracted["values"],
        }]

    # Save file + extraction result for future OCR training (fire-and-forget)
    try:
        _save_template_sample(file_bytes, content_type, detected_lab, extracted)
    except Exception:
        pass  # Never block the response for template saving

    return {
        "lab_name": detected_lab,
        "report_number": extracted.get("report_number"),
        "analysis_date": extracted.get("analysis_date"),
        "client": extracted.get("client"),
        "department": extracted.get("department"),
        "num_samples": len(samples),
        "ai_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
            "model": "claude-sonnet-4-20250514",
        },
        "samples": samples,
        # Keep backward-compatible single "values" for single-sample reports
        "values": samples[0]["values"] if len(samples) == 1 else {},
        "has_template": lab_template is not None,
        "template_sample_count": lab_template.get("sample_count", 0) if lab_template else 0,
    }


def learn_from_corrections(
    lab_name: str,
    original_values: dict[str, Any],
    corrected_values: dict[str, Any],
) -> dict[str, Any]:
    """Learn field mappings from user corrections.

    Compares original extracted values with user-corrected values to build
    a mapping of lab-specific field names to our standard parameter names.
    """
    if not lab_name:
        return {"updated": False, "reason": "No lab name provided"}

    sb = get_supabase_admin()

    # Get or create lab template
    result = sb.table("lab_templates").select("*").eq("lab_name", lab_name).execute()
    existing = result.data[0] if result.data else None

    field_mappings = existing["field_mappings"] if existing else {}

    # Find corrections: values that were changed or added
    changes = 0
    for param, corrected_val in corrected_values.items():
        original_val = original_values.get(param)
        if original_val != corrected_val and corrected_val is not None:
            # The user corrected this value — record the mapping
            # We store the original lab field name → our standard name
            field_mappings[param] = param
            changes += 1

    if existing:
        sb.table("lab_templates").update({
            "field_mappings": field_mappings,
            "sample_count": (existing.get("sample_count") or 0) + 1,
            "last_used": "now()",
        }).eq("id", existing["id"]).execute()
    else:
        sb.table("lab_templates").insert({
            "lab_name": lab_name,
            "field_mappings": field_mappings,
            "sample_count": 1,
        }).execute()

    return {
        "updated": True,
        "lab_name": lab_name,
        "corrections_recorded": changes,
        "total_mappings": len(field_mappings),
    }


def _get_lab_template(lab_name: str) -> dict | None:
    """Fetch a lab template by name (case-insensitive partial match)."""
    sb = get_supabase_admin()
    try:
        result = sb.table("lab_templates").select("*").ilike("lab_name", f"%{lab_name}%").limit(1).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


def _save_template_sample(
    file_bytes: bytes,
    content_type: str,
    lab_name: str,
    extraction_result: dict,
) -> None:
    """Save the original file and extraction result to Supabase Storage + lab_templates.

    Stored for future OCR engine training. Each file gets a unique path under
    lab-reports/{lab_name_slug}/{timestamp}.{ext}
    """
    import hashlib
    from datetime import datetime

    if not lab_name:
        return

    sb = get_supabase_admin()

    # Generate file path
    dept = (extraction_result.get("department") or "unknown").lower().replace(" ", "-")[:20]
    slug = lab_name.lower().replace(" ", "-").replace("/", "-")[:50]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = {
        "application/pdf": "pdf",
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }.get(content_type, "bin")
    file_hash = hashlib.md5(file_bytes).hexdigest()[:8]
    storage_path = f"{slug}/{dept}/{ts}_{file_hash}.{ext}"

    # Upload file to storage
    sb.storage.from_("lab-reports").upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": content_type},
    )

    # Update lab_templates with the file reference and extraction layout
    # Use lab_name + department as key so soil and leaf get separate templates
    template_name = f"{lab_name} ({dept})" if dept != "unknown" else lab_name
    result = sb.table("lab_templates").select("*").eq("lab_name", template_name).limit(1).execute()
    if not result.data:
        # Fall back to matching without department
        result = sb.table("lab_templates").select("*").ilike("lab_name", f"%{lab_name}%").limit(1).execute()

    # Extract layout hints from the result (column order, header names, etc.)
    layout_data = {
        "department": extraction_result.get("department"),
        "num_samples": len(extraction_result.get("samples", [])),
        "column_headers": [],
        "sample_fields": [],
    }
    samples = extraction_result.get("samples", [])
    if samples:
        # Record what fields were found (this is the "layout" of the report)
        layout_data["sample_fields"] = list(samples[0].get("values", {}).keys())
        layout_data["has_block_name"] = any(s.get("block_name") for s in samples)
        layout_data["has_crop"] = any(s.get("crop") for s in samples)
        layout_data["has_cultivar"] = any(s.get("cultivar") for s in samples)

    if result.data:
        existing = result.data[0]
        sample_files = existing.get("sample_files") or []
        sample_files.append(storage_path)
        # Keep max 20 samples per lab (oldest get pushed out)
        if len(sample_files) > 20:
            sample_files = sample_files[-20:]

        sb.table("lab_templates").update({
            "sample_files": sample_files,
            "layout_data": layout_data,
            "sample_count": (existing.get("sample_count") or 0) + 1,
            "last_used": "now()",
        }).eq("id", existing["id"]).execute()
    else:
        sb.table("lab_templates").insert({
            "lab_name": template_name,
            "field_mappings": {},
            "sample_files": [storage_path],
            "layout_data": layout_data,
            "sample_count": 1,
        }).execute()
