"""Router-level unit tests for /api/programmes/v2 helpers."""
from __future__ import annotations

from app.models import OutstandingItem
from app.routers.programmes_v2 import (
    SkippedBlockRequest,
    _append_skipped_block_items,
)


class _StubArtifact:
    """Minimal stand-in for ProgrammeArtifact — all we need is a mutable
    outstanding_items list. Lets us test the skipped-block wiring without
    building a full artifact via the orchestrator.
    """
    def __init__(self) -> None:
        self.outstanding_items: list[OutstandingItem] = []


def test_append_skipped_block_items_empty_input_is_noop():
    artifact = _StubArtifact()
    _append_skipped_block_items(artifact, [])
    assert artifact.outstanding_items == []


def test_append_skipped_block_items_adds_one_per_block():
    artifact = _StubArtifact()
    skipped = [
        SkippedBlockRequest(block_name="Land A", reason="no soil analysis linked"),
        SkippedBlockRequest(block_name="Pivot 2", reason="no soil analysis linked"),
    ]
    _append_skipped_block_items(artifact, skipped)

    assert len(artifact.outstanding_items) == 2
    names = [item.item for item in artifact.outstanding_items]
    assert any("Land A" in n for n in names)
    assert any("Pivot 2" in n for n in names)


def test_append_skipped_block_items_includes_reason_and_guidance():
    artifact = _StubArtifact()
    skipped = [SkippedBlockRequest(block_name="Land C", reason="custom reason here")]
    _append_skipped_block_items(artifact, skipped)

    item = artifact.outstanding_items[0]
    assert "Land C" in item.item
    assert "custom reason here" in item.item
    # why_it_matters + impact_if_skipped guide the agronomist
    assert item.why_it_matters
    assert item.impact_if_skipped
    assert "soil analysis" in (item.impact_if_skipped or "").lower()


def test_append_skipped_block_items_preserves_existing_items():
    artifact = _StubArtifact()
    existing = OutstandingItem(
        item="Existing item",
        why_it_matters="unrelated prior finding",
    )
    artifact.outstanding_items.append(existing)

    _append_skipped_block_items(artifact, [
        SkippedBlockRequest(block_name="Land D", reason="no soil analysis linked"),
    ])

    assert len(artifact.outstanding_items) == 2
    assert artifact.outstanding_items[0] is existing
    assert "Land D" in artifact.outstanding_items[1].item
