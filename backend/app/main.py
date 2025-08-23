from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="trpg-supporter")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요 시 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 Router
router = APIRouter(prefix="/api/v1")


@router.get("/healthz")
async def healthz():
    return {"ok": True}


# (필요 시) 실제 엔드포인트 라우터 추가
# from backend.app.api.v1.characters import router as characters_router
# router.include_router(characters_router)

# 최종 등록
app.include_router(router)
