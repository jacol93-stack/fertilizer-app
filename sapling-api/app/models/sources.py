"""
Source registry + citation types.

Every numeric recommendation in a programme output carries a SourceCitation
that resolves against a canonical Source registry. The registry formalises
what was implicit across the rate-table seeding migrations (046-069).
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    """A canonical reference source for agronomic data.

    Examples:
        Source(id="FERTASA_5_6_1", name="FERTASA Handbook", section="5.6.1",
               title="General Vegetables", year=2019, tier=1, url=None)
        Source(id="SAMAC_SCHOEMAN_2021", name="SAMAC", section="3.2",
               title="Macadamia Fertilisation Guide", year=2021, tier=1)
        Source(id="ARC_GCI_MIG_2017_T2", name="ARC-GCI", section="Table 2",
               title="Maize Information Guide 2017", year=2017, tier=2)
    """

    id: str = Field(..., description="Stable identifier, e.g. FERTASA_5_6_1")
    name: str = Field(..., description="Organisation/publisher")
    section: Optional[str] = Field(None, description="Section or table reference")
    title: Optional[str] = Field(None, description="Publication title")
    year: Optional[int] = Field(None, ge=1900, le=2100)
    tier: int = Field(..., ge=1, le=6, description="See Tier enum")
    url: Optional[str] = None
    notes: Optional[str] = None


class SourceRegistry:
    """In-memory registry of canonical sources.

    Populated at app startup from the DB (planned Phase 6 migration creates
    a source_registry table). For now this is a placeholder — Phase 2 will
    populate with actual data.
    """

    _sources: dict[str, Source] = {}

    @classmethod
    def register(cls, source: Source) -> None:
        cls._sources[source.id] = source

    @classmethod
    def get(cls, source_id: str) -> Optional[Source]:
        return cls._sources.get(source_id)

    @classmethod
    def all(cls) -> list[Source]:
        return list(cls._sources.values())

    @classmethod
    def clear(cls) -> None:
        """Testing helper."""
        cls._sources.clear()
