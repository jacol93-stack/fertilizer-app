"""Pagination + list-response helpers.

Every list endpoint in the API returns a `Page[T]` envelope so the
frontend can render "Showing 1-20 of 847" and wire Previous/Next
controls without guessing at the total.

Usage (router side):

    from app.pagination import Page, PageParams, apply_page

    @router.get("/")
    def list_things(
        page: PageParams = Depends(PageParams.as_query),
        user: CurrentUser = Depends(get_current_user),
    ) -> Page[ThingOut]:
        sb = get_supabase_admin()
        # count="exact" populates result.count for the envelope total.
        q = sb.table("things").select("*", count="exact").eq("agent_id", user.id)
        q = apply_page(q, page, default_order="created_at")
        result = q.execute()
        return Page.from_result(result, page)

Usage (frontend side): expect `{items, total, skip, limit}` in responses
that declare `Page[...]` as their return type. See
`sapling-web/src/lib/pagination.ts`.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

T = TypeVar("T")

# Hard ceiling on page size so a client can't DoS the API with limit=1e6.
MAX_LIMIT = 500
DEFAULT_LIMIT = 20


class PageParams(BaseModel):
    """Query-string pagination + ordering. Declare as a FastAPI dependency.

    Because Pydantic v2 models can't be used directly as FastAPI query
    dependencies (they bind as a request body), use the `as_query`
    classmethod as the dependency: `Depends(PageParams.as_query)`.
    """

    skip: int = Field(0, ge=0, description="Rows to skip (offset)")
    limit: int = Field(
        DEFAULT_LIMIT, ge=1, le=MAX_LIMIT,
        description=f"Rows to return (1-{MAX_LIMIT})",
    )
    order_by: str | None = Field(
        None,
        description="Column to order by; endpoint supplies a default.",
    )
    order_desc: bool = Field(True, description="Descending if true")

    @classmethod
    def as_query(
        cls,
        skip: int = Query(0, ge=0),
        limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
        order_by: str | None = Query(None),
        order_desc: bool = Query(True),
    ) -> "PageParams":
        return cls(skip=skip, limit=limit, order_by=order_by, order_desc=order_desc)


class Page(BaseModel, Generic[T]):
    """List-response envelope.

    Shape the frontend expects:
        { "items": [...], "total": 847, "skip": 0, "limit": 20 }

    `total` can be None if the underlying query didn't request a count;
    callers should pass `count="exact"` into the Supabase select to get a
    populated total.
    """

    items: list[T]
    total: int | None = None
    skip: int
    limit: int

    @classmethod
    def from_result(cls, result: Any, params: PageParams) -> "Page[T]":
        """Build a Page from a Supabase execute() result.

        Works whether the query used `count="exact"` (sets `.count`) or
        didn't (we fall back to `len(items)` — approximate but usable).
        """
        data = getattr(result, "data", None) or []
        count = getattr(result, "count", None)
        if count is None:
            count = len(data)
        return cls(items=data, total=count, skip=params.skip, limit=params.limit)

    @classmethod
    def from_list(cls, items: list[T], params: PageParams, total: int | None = None) -> "Page[T]":
        """Build a Page from an already-materialised list (e.g. after
        post-processing). Caller supplies the total separately."""
        return cls(
            items=items,
            total=total if total is not None else len(items),
            skip=params.skip,
            limit=params.limit,
        )


def apply_page(query: Any, params: PageParams, *, default_order: str = "created_at") -> Any:
    """Attach ordering + offset + limit to a Supabase query builder.

    The endpoint supplies a per-resource default_order (usually
    "created_at" for time-series resources, "name" for alphabetised
    lists). The client can override via the `order_by` query param.
    Unknown column names will raise from Supabase at execute time — that
    is the caller's responsibility to guard if they want a whitelist.
    """
    order_col = params.order_by or default_order
    query = query.order(order_col, desc=params.order_desc)
    # Supabase-py uses `range(start, end)` inclusive; use .offset/.limit
    # for clarity. Both are equivalent.
    if params.skip:
        query = query.offset(params.skip)
    query = query.limit(params.limit)
    return query
