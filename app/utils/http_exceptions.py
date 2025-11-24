from typing import NoReturn

from fastapi import HTTPException


def http_error(status_code: int, code: str, message: str) -> NoReturn:
    """Raise HTTPException with unified error payload."""
    raise HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": message}},
    )
