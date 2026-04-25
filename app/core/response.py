from __future__ import annotations

from typing import Any


def success_response(data: Any, message: str = "Success", status_code: int = 200) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
        "status_code": status_code,
    }
