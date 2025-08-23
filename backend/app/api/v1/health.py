from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz():
    # 테스트가 {"status":"ok"} 형태를 기대합니다.
    return {"status": "ok"}
