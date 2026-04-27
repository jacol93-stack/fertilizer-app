"""Leaf/sap analysis router: classify, save, recommend foliar corrections."""

import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user, require_admin
from app.pagination import Page, PageParams, apply_page
from app.supabase_client import get_supabase_admin, run_sb

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Leaf Analysis"])


class LeafClassifyRequest(BaseModel):
    crop: str | None = Field(None, max_length=200)
    values: dict[str, float] = Field(..., description="Element concentrations e.g. {'N': 2.5, 'P': 0.18}")


class LeafSaveRequest(BaseModel):
    client_id: str | None = None
    farm_id: str | None = None
    field_id: str | None = None
    programme_id: str | None = None
    block_id: str | None = None
    crop: str = Field(..., min_length=1, max_length=200)
    sample_part: str | None = Field(None, max_length=200)
    sample_date: str | None = None
    lab_name: str | None = Field(None, max_length=200)
    values: dict[str, float]
    classifications: dict | None = None
    recommendations: dict | None = None
    foliar_recommendations: dict | None = None
    notes: str | None = None


def _audit(sb, user, action, record_id=None, detail=None):
    try:
        sb.rpc("log_audit_event", {
            "p_event_type": action,
            "p_entity_type": "leaf_analyses",
            "p_entity_id": record_id,
            "p_metadata": detail or {},
            "p_user_id": user.id,
        }).execute()
    except Exception as _audit_exc:
        import logging as _logging
        _logging.getLogger("sapling.audit").debug(
            "log_audit_event failed: %s", _audit_exc, extra={"event_type": action}
        )


@router.post("/classify")
def classify_leaf(body: LeafClassifyRequest, user: CurrentUser = Depends(get_current_user)):
    """Classify leaf analysis values against Fertasa norms.

    Returns classifications (Deficient/Low/Sufficient/High/Excess) per element
    plus deficiency details and foliar spray recommendations.
    """
    from app.services.leaf_engine import classify_leaf_values, generate_leaf_recommendations

    result = classify_leaf_values(body.crop, body.values)

    # Generate recommendations including foliar sprays
    recs = generate_leaf_recommendations(
        crop=body.crop,
        classifications=result["classifications"],
        deficiencies=result["deficiencies"],
    )

    sb = get_supabase_admin()
    _audit(sb, user, "leaf_classify", detail={"crop": body.crop or "unknown", "elements": len(body.values)})

    return {
        **result,
        **recs,
    }


@router.post("/", status_code=201)
def save_leaf_analysis(body: LeafSaveRequest, user: CurrentUser = Depends(get_current_user)):
    """Save a leaf analysis record."""
    sb = get_supabase_admin()

    data = body.model_dump(exclude_none=True)
    data["agent_id"] = user.id

    result = sb.table("leaf_analyses").insert(data).execute()
    if not result.data:
        raise HTTPException(500, "Failed to save leaf analysis")

    record = result.data[0]
    _audit(sb, user, "leaf_save", record["id"], {"crop": body.crop})

    # Adjustment-detection on save was previously coupled to the v1
    # programme tables. Phase 4 will rebuild this on v2 ProgrammeArtifact.

    return record


@router.get("/")
def list_leaf_analyses(
    page: PageParams = Depends(PageParams.as_query),
    user: CurrentUser = Depends(get_current_user),
    client_id: str | None = None,
    field_id: str | None = None,
):
    """List leaf analyses. Agents see own, admins see all."""
    sb = get_supabase_admin()
    query = sb.table("leaf_analyses").select("*", count="exact").is_("deleted_at", "null")
    if user.role != "admin":
        query = query.eq("agent_id", user.id)
    if client_id:
        query = query.eq("client_id", client_id)
    if field_id:
        query = query.eq("field_id", field_id)
    query = apply_page(query, page, default_order="created_at")
    return Page.from_result(run_sb(lambda: query.execute()), page)


@router.get("/{analysis_id}")
def get_leaf_analysis(analysis_id: str, user: CurrentUser = Depends(get_current_user)):
    """Get a leaf analysis by ID."""
    sb = get_supabase_admin()
    result = run_sb(lambda: sb.table("leaf_analyses").select("*").eq("id", analysis_id).execute())
    if not result.data:
        raise HTTPException(404, "Leaf analysis not found")
    record = result.data[0]
    if record["agent_id"] != user.id and user.role != "admin":
        raise HTTPException(403, "Access denied")
    return record


@router.get("/sampling-guide/{crop}")
def get_sampling_guide(crop: str, user: CurrentUser = Depends(get_current_user)):
    """Get Fertasa sampling guide for a crop (what to sample, when, how)."""
    from app.services.leaf_engine import get_sampling_guide as _get_guide
    guide = _get_guide(crop)
    if not guide:
        return {"crop": crop, "guide": None, "message": f"No sampling guide available for {crop}"}
    return guide


# NOTE: /link-programme endpoint removed with the v1 programmes rip-out.
# Phase 4 will reintroduce leaf→programme linkage on v2 ProgrammeArtifact.


@router.post("/{analysis_id}/delete", status_code=200)
def soft_delete_leaf_analysis(analysis_id: str, user: CurrentUser = Depends(get_current_user)):
    """Soft-delete a leaf analysis (mark as deleted)."""
    sb = get_supabase_admin()

    existing = sb.table("leaf_analyses").select("id, agent_id").eq("id", analysis_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Leaf analysis not found")
    if user.role != "admin" and existing.data[0].get("agent_id") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    now = datetime.now(timezone.utc).isoformat()
    sb.table("leaf_analyses").update({
        "deleted_at": now,
        "deleted_by": user.id,
    }).eq("id", analysis_id).execute()

    _audit(sb, user, "soft_delete", analysis_id)
    return {"detail": "Leaf analysis soft-deleted"}


@router.post("/{analysis_id}/restore", status_code=200)
def restore_leaf_analysis(analysis_id: str, user: CurrentUser = Depends(require_admin)):
    """Admin only. Restore a soft-deleted leaf analysis."""
    sb = get_supabase_admin()
    result = sb.table("leaf_analyses").update({
        "deleted_at": None,
        "deleted_by": None,
    }).eq("id", analysis_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Leaf analysis not found")

    _audit(sb, user, "restore", analysis_id)
    return {"detail": "Leaf analysis restored"}


@router.get("/{analysis_id}/document")
def get_leaf_document(analysis_id: str, user: CurrentUser = Depends(get_current_user)):
    """Get a signed URL for the original lab report document."""
    sb = get_supabase_admin()

    result = sb.table("leaf_analyses").select("source_document_url, agent_id").eq("id", analysis_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Leaf analysis not found")

    record = result.data[0]
    if user.role != "admin" and record.get("agent_id") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    doc_url = record.get("source_document_url")
    if not doc_url:
        raise HTTPException(status_code=404, detail="No document attached to this analysis")

    signed = sb.storage.from_("lab-reports").create_signed_url(doc_url, 300)
    return {"url": signed.get("signedURL") or signed.get("signedUrl", "")}


class LinkFieldRequest(BaseModel):
    field_id: str


@router.post("/{analysis_id}/link-field")
def link_leaf_to_field(
    analysis_id: str,
    body: LinkFieldRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Link a leaf analysis to a field. Mirrors the soil link-field endpoint
    so the documents tray can relink either type via the same flow."""
    sb = get_supabase_admin()

    result = sb.table("leaf_analyses").select("id, agent_id").eq("id", analysis_id).execute()
    if not result.data:
        raise HTTPException(404, "Leaf analysis not found")
    if user.role != "admin" and result.data[0].get("agent_id") != user.id:
        raise HTTPException(403, "Access denied")

    field_result = sb.table("fields").select("name, farm_id").eq("id", body.field_id).execute()
    if not field_result.data:
        raise HTTPException(404, "Field not found")

    farm_id = field_result.data[0].get("farm_id")

    sb.table("leaf_analyses").update({
        "field_id": body.field_id,
        "farm_id": farm_id,
    }).eq("id", analysis_id).execute()

    _audit(sb, user, "link_field", analysis_id, {"field_id": body.field_id})

    return {"ok": True}


@router.post("/extract")
async def extract_leaf_report(
    file: UploadFile = File(...),
    lab_name_hint: str | None = Form(None),
    client_id: str | None = Form(None),
    user: CurrentUser = Depends(get_current_user),
):
    """Extract leaf analysis values from an uploaded lab report (PDF or photo).

    Mirrors /api/soil/extract — same Claude vision pipeline, same lab-template
    learning, same document persistence — but selects the leaf parameter set
    (macros in %, micros in mg/kg) and adds leaf-specific guidance.
    """
    from app.services.lab_extractor import extract_from_document

    allowed_types = {
        "application/pdf", "image/jpeg", "image/png", "image/webp", "image/gif",
    }
    if file.content_type not in allowed_types:
        raise HTTPException(
            400, f"Unsupported file type: {file.content_type}. Upload a PDF or image."
        )

    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum 50 MB.")

    try:
        result = extract_from_document(contents, file.content_type, lab_name_hint, mode="leaf")
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.exception(
            "leaf extract failed for user %s (%s, %d bytes)",
            user.id, file.content_type, len(contents),
        )
        raise HTTPException(500, f"Extraction failed: {str(e)}")

    sb = get_supabase_admin()

    source_document_url = None
    try:
        ext = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(
            file.content_type, "bin",
        )
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(contents).hexdigest()[:8]
        owner = client_id or user.id
        storage_path = f"clients/{owner}/leaf_{ts}_{file_hash}.{ext}"
        sb.storage.from_("lab-reports").upload(
            path=storage_path,
            file=contents,
            file_options={"content-type": file.content_type},
        )
        source_document_url = storage_path
    except Exception as e:
        logger.warning("lab-report storage upload failed for user %s: %s", user.id, e)

    _audit(sb, user, "lab_extract_leaf", detail={
        "lab_name": result.get("lab_name"),
        "num_samples": result.get("num_samples", 0),
        "file_type": file.content_type,
    })

    ai_usage = result.get("ai_usage")
    if ai_usage:
        try:
            sb.table("ai_usage").insert({
                "user_id": user.id,
                "operation": "extract_leaf",
                "model": ai_usage.get("model", ""),
                "input_tokens": ai_usage.get("input_tokens", 0),
                "output_tokens": ai_usage.get("output_tokens", 0),
                "cost_usd": ai_usage.get("cost_usd", 0),
                "metadata": {
                    "lab_name": result.get("lab_name"),
                    "num_samples": result.get("num_samples", 0),
                    "file_type": file.content_type,
                },
            }).execute()
        except Exception as e:
            logger.warning("ai_usage insert failed for user %s: %s", user.id, e)

    if source_document_url:
        result["source_document_url"] = source_document_url

    return result
