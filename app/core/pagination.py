from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    limit: int
    pages: int


def paginate(items: list[Any], page: int, limit: int) -> PaginatedResponse:
    safe_page = max(page, 1)
    safe_limit = min(max(limit, 1), 100)
    total = len(items)
    pages = math.ceil(total / safe_limit) if total > 0 else 0
    start = (safe_page - 1) * safe_limit
    end = start + safe_limit
    return PaginatedResponse(
        items=items[start:end],
        total=total,
        page=safe_page,
        limit=safe_limit,
        pages=pages,
    )
