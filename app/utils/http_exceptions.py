from fastapi import HTTPException


def http_error(status_code: int, code: str, message: str) -> None:
    """Raise HTTPException with unified error payload."""
    raise HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": message}},
    )

