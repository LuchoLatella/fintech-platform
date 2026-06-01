from fastapi import APIRouter

router = APIRouter(
prefix="/auth",
tags=["Authentication"]
)

@router.get("/health")
async def health():
return {
"status": "ok"
}

