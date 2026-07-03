from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "BrallGPT API",
        "time": datetime.now(timezone.utc).isoformat(),
    }
