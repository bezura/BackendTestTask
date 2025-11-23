from fastapi import APIRouter
from starlette import status
from starlette.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})
