"""Opus narrative pipeline.

Engine owns determinism. AI owns prose. One-way only — facts → prose,
never prose → facts. See `memory/project_ai_integration_direction.md`
for the locked architecture.

Public surface:

    from app.services.narrative import enhance_artifact_prose

    enhanced = enhance_artifact_prose(artifact, mode="client")
    # → dict[str, str] of section-keyed prose overrides; empty dict on
    #   fallback (engine prose used as-is).

The enhance call runs three layers of defense:

  1. Per-section Opus generation (`opus_renderer`)
  2. Fact validator — every number traces to artifact
  3. Policeman — denylist + rate caps + Opus critique → PASS/WARN/FAIL

FAIL → empty dict returned (deterministic prose used).
WARN → prose returned, verdict logged for admin review.
PASS → prose returned cleanly.
"""
from app.services.narrative.opus_renderer import enhance_artifact_prose

__all__ = ["enhance_artifact_prose"]
